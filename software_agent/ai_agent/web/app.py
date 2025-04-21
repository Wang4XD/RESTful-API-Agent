from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
import json
import jwt
import datetime

from ..config import WEB_CONFIG, BASE_CONFIG
from ..agent.llm_processor import LLMProcessor
from ..agent.intent_parser import IntentParser
from ..agent.tool_manager import ToolManager
from ..api.api_client import APIClient
from ..utils.logger import setup_logger



# 定义请求模型
class UserRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AuthRequest(BaseModel):
    username: str
    password: str


# 定义响应模型
class Response(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# 创建应用
app = FastAPI(
    title="AI Agent API",
    description="将自然语言请求转换为软件API调用的AI代理",
    version=BASE_CONFIG["version"]
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=WEB_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 初始化日志记录器
logger = setup_logger("web_app", log_level=BASE_CONFIG["log_level"])


# 创建依赖项
def get_api_client() -> APIClient:
    return APIClient()


def get_llm_processor() -> LLMProcessor:
    return LLMProcessor()


def get_intent_parser(llm_processor: LLMProcessor = Depends(get_llm_processor)) -> IntentParser:
    return IntentParser(llm_processor)


def get_tool_manager(api_client: APIClient = Depends(get_api_client)) -> ToolManager:
    return ToolManager(api_client)


# 会话存储(简易实现，生产环境应使用Redis等)
conversation_history = {}


# 验证令牌
async def verify_token(token: str = Depends(oauth2_scheme)):
    if not WEB_CONFIG["auth_required"]:
        return {"sub": "anonymous"}

    try:
        payload = jwt.decode(
            token,
            WEB_CONFIG["jwt_secret"],
            algorithms=[WEB_CONFIG["jwt_algorithm"]]
        )
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 定义路由
@app.post("/api/auth/token")
async def login(auth_data: AuthRequest):
    """用户登录并获取令牌"""
    # 在实际应用中，替换为真实的用户验证逻辑

    # 模拟用户验证
    if auth_data.username == "demo" and auth_data.password == "password":
        # 创建访问令牌
        access_token_expires = datetime.timedelta(seconds=WEB_CONFIG["jwt_expiration"])
        expires = datetime.datetime.utcnow() + access_token_expires

        # 令牌数据
        token_data = {
            "sub": auth_data.username,
            "exp": expires
        }

        # 生成令牌
        access_token = jwt.encode(
            token_data,
            WEB_CONFIG["jwt_secret"],
            algorithm=WEB_CONFIG["jwt_algorithm"]
        )

        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires": expires.isoformat()
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/api/process")
async def process_message(
        request: UserRequest,
        user: Dict = Depends(verify_token),
        intent_parser: IntentParser = Depends(get_intent_parser),
        tool_manager: ToolManager = Depends(get_tool_manager)
):
    """处理用户消息并执行相应操作"""
    try:
        # 获取对话历史
        conversation_id = request.conversation_id
        context = []

        if conversation_id and conversation_id in conversation_history:
            context = conversation_history[conversation_id]
        elif conversation_id:
            # 新建对话
            conversation_history[conversation_id] = []
            context = conversation_history[conversation_id]

        # 解析用户意图
        intent_result = intent_parser.parse_intent(request.message, context)

        # 添加到对话历史
        if conversation_id:
            context.append({"role": "user", "content": request.message})

        # 处理解析结果
        if not intent_result["success"]:
            # 需要澄清意图
            if intent_result.get("clarification_needed", False):
                clarification_msg = "我需要更多信息来帮助你：\n"
                questions = intent_result.get("clarification_questions", [])
                for i, question in enumerate(questions, 1):
                    clarification_msg += f"{i}. {question}\n"

                # 添加到对话历史
                if conversation_id:
                    context.append({"role": "assistant", "content": clarification_msg})

                return {
                    "success": True,
                    "message": clarification_msg,
                    "data": {
                        "requires_clarification": True,
                        "confidence": intent_result.get("confidence", 0)
                    }
                }
            else:
                # 解析错误
                error_msg = f"很抱歉，我无法理解你的请求：{intent_result.get('error', '未知错误')}"

                # 添加到对话历史
                if conversation_id:
                    context.append({"role": "assistant", "content": error_msg})

                return {
                    "success": False,
                    "message": error_msg,
                    "error": intent_result.get("error", "未知错误")
                }

        # 提取操作和参数
        action = intent_result["action"]
        parameters = intent_result["parameters"]

        # 执行工具
        tool_result = tool_manager.execute_tool(action, parameters)

        if not tool_result["success"]:
            # 工具执行失败
            error_msg = f"执行操作失败：{tool_result.get('error', '未知错误')}"

            # 添加到对话历史
            if conversation_id:
                context.append({"role": "assistant", "content": error_msg})

            return {
                "success": False,
                "message": error_msg,
                "error": tool_result.get("error", "未知错误"),
                "data": tool_result.get("details", {})
            }

        # 执行成功，生成自然语言响应
        result_data = tool_result["result"]

        # 根据操作类型生成响应消息
        response_msg = generate_response_message(action, result_data)

        # 添加到对话历史
        if conversation_id:
            context.append({"role": "assistant", "content": response_msg})

        return {
            "success": True,
            "message": response_msg,
            "data": {
                "action": action,
                "result": result_data
            }
        }

    except Exception as e:
        logger.error(f"处理消息异常: {str(e)}")
        return {
            "success": False,
            "message": "处理请求时发生错误",
            "error": str(e)
        }


@app.post("/api/conversations")
async def create_conversation(user: Dict = Depends(verify_token)):
    """创建新对话"""
    conversation_id = f"conv_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{len(conversation_history) + 1}"
    conversation_history[conversation_id] = []

    return {
        "success": True,
        "message": "对话创建成功",
        "data": {"conversation_id": conversation_id}
    }


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: Dict = Depends(verify_token)):
    """获取对话历史"""
    if conversation_id not in conversation_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    return {
        "success": True,
        "message": "获取对话历史成功",
        "data": {"history": conversation_history[conversation_id]}
    }


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: Dict = Depends(verify_token)):
    """删除对话"""
    if conversation_id not in conversation_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )

    del conversation_history[conversation_id]

    return {
        "success": True,
        "message": "对话删除成功"
    }


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": BASE_CONFIG["version"]}


# 辅助函数
def generate_response_message(action: str, result_data: Dict[str, Any]) -> str:
    """根据操作类型和结果生成自然语言响应"""

    # 用户相关操作
    if action == "login":
        return "登录成功！欢迎回来。"
    elif action == "logout":
        return "您已成功退出系统。"
    elif action == "get_user":
        user = result_data
        return f"用户信息: 用户名 {user.get('username', '未知')}, 邮箱 {user.get('email', '未知')}"
    elif action == "create_user":
        return f"用户创建成功！用户ID: {result_data.get('id', '未知')}"
    elif action == "update_user":
        return "用户信息已成功更新。"
    elif action == "delete_user":
        return "用户已成功删除。"

    # 项目相关操作
    elif action == "list_projects":
        projects = result_data.get("projects", [])
        count = len(projects)
        if count == 0:
            return "没有找到任何项目。"
        elif count == 1:
            return f"找到1个项目: {projects[0].get('name', '未命名项目')}"
        else:
            project_names = [p.get('name', '未命名项目') for p in projects[:3]]
            return f"找到{count}个项目。包括: {', '.join(project_names)}" + ("..." if count > 3 else "")
    elif action == "get_project":
        project = result_data
        return f"项目详情: {project.get('name', '未命名项目')} - {project.get('description', '无描述')}"
    elif action == "create_project":
        return f"项目创建成功！项目ID: {result_data.get('id', '未知')}"
    elif action == "update_project":
        return "项目信息已成功更新。"
    elif action == "delete_project":
        return "项目已成功删除。"

    # 文件相关操作
    elif action == "list_files":
        files = result_data.get("files", [])
        count = len(files)
        if count == 0:
            return "该项目中没有找到任何文件。"
        elif count == 1:
            return f"找到1个文件: {files[0].get('name', '未命名文件')}"
        else:
            file_names = [f.get('name', '未命名文件') for f in files[:3]]
            return f"找到{count}个文件。包括: {', '.join(file_names)}" + ("..." if count > 3 else "")
    elif action == "upload_file":
        return f"文件上传成功！文件ID: {result_data.get('id', '未知')}"
    elif action == "download_file":
        return "文件已准备好下载。"
    elif action == "delete_file":
        return "文件已成功删除。"

    # 数据分析相关操作
    elif action == "run_analysis":
        return f"分析任务已成功启动。分析ID: {result_data.get('analysis_id', '未知')}"
    elif action == "get_analysis_result":
        status = result_data.get("status", "未知")
        if status.lower() == "completed":
            return "分析已完成，结果已可用。"
        elif status.lower() == "running":
            return "分析正在进行中，请稍后查询结果。"
        elif status.lower() == "failed":
            return f"分析任务失败: {result_data.get('error', '未知错误')}"
        else:
            return f"分析状态: {status}"
    elif action == "export_report":
        return "报告已成功导出，可以下载。"

    # 系统相关操作
    elif action == "get_system_status":
        status = result_data.get("status", "未知")
        return f"系统状态: {status}"
    elif action == "get_usage_statistics":
        return "已获取使用统计数据。"

    # 默认响应
    else:
        return f"操作 '{action}' 已成功执行。"


@app.get("/")
async def root():
    return {"message": "欢迎使用 Software AI Agent", "version": BASE_CONFIG["version"]}

    # 主入口
if __name__ == "__main__":
    # 运行FastAPI应用
    uvicorn.run(
        "app:app",
        host=WEB_CONFIG["host"],
        port=WEB_CONFIG["port"],
        reload=BASE_CONFIG["debug"]
    )
