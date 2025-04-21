from typing import Dict, Any, List, Optional, Tuple

from ..config import BASE_CONFIG
from ..utils.logger import setup_logger
from .llm_processor import LLMProcessor


class IntentParser:
    """解析用户意图并转换为API操作"""

    def __init__(self, llm_processor: LLMProcessor = None):
        self.llm_processor = llm_processor or LLMProcessor()
        self.logger = setup_logger("intent_parser", log_level=BASE_CONFIG["log_level"])

        # 定义意图到API操作的映射
        self.intent_map = {
            # 用户管理意图
            "登录": "login",
            "退出": "logout",
            "获取用户信息": "get_user",
            "创建用户": "create_user",
            "更新用户": "update_user",
            "删除用户": "delete_user",

            # 项目管理意图
            "查看所有项目": "list_projects",
            "获取项目信息": "get_project",
            "创建项目": "create_project",
            "更新项目": "update_project",
            "删除项目": "delete_project",

            # 文件管理意图
            "查看文件列表": "list_files",
            "上传文件": "upload_file",
            "下载文件": "download_file",
            "删除文件": "delete_file",

            # 数据处理意图
            "运行分析": "run_analysis",
            "获取分析结果": "get_analysis_result",
            "导出报告": "export_report",

            # 系统操作意图
            "查看系统状态": "get_system_status",
            "获取使用统计": "get_usage_statistics",
        }

    def parse_intent(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        解析用户意图并提取参数

        Args:
            user_input: 用户的自然语言输入
            context: 可选的对话上下文

        Returns:
            含有解析结果的字典
        """
        # 使用LLM处理输入
        llm_response = self.llm_processor.process_input(user_input, context)

        if "error" in llm_response:
            self.logger.error(f"LLM处理错误: {llm_response.get('error')}")
            return {
                "success": False,
                "error": llm_response.get("error"),
                "raw_response": llm_response
            }

        # 验证LLM响应格式
        required_fields = ["action", "parameters"]
        missing_fields = [field for field in required_fields if field not in llm_response]

        if missing_fields:
            self.logger.warning(f"LLM响应缺少必要字段: {missing_fields}")
            return {
                "success": False,
                "error": f"解析响应缺少字段: {', '.join(missing_fields)}",
                "raw_response": llm_response
            }

        action = llm_response["action"]
        parameters = llm_response["parameters"]
        confidence = llm_response.get("confidence", 0.0)

        # 检查置信度
        if confidence < 0.7:  # 可调整阈值
            clarification = llm_response.get("clarification_questions", [])
            self.logger.info(f"低置信度({confidence}), 需要澄清: {clarification}")
            return {
                "success": False,
                "error": "置信度不足",
                "confidence": confidence,
                "clarification_needed": True,
                "clarification_questions": clarification,
                "raw_response": llm_response
            }

        # 查找匹配的API操作
        api_action = self._map_to_api_action(action)
        if not api_action:
            self.logger.warning(f"未能映射意图 '{action}' 到API操作")
            return {
                "success": False,
                "error": f"未支持的操作: {action}",
                "raw_response": llm_response
            }

        return {
            "success": True,
            "action": api_action,
            "parameters": parameters,
            "confidence": confidence,
            "raw_response": llm_response
        }

    def _map_to_api_action(self, intent: str) -> Optional[str]:
        """
        将意图映射到API操作

        Args:
            intent: 用户意图

        Returns:
            对应的API操作名，或None(如无匹配)
        """
        # 直接匹配
        if intent in self.intent_map:
            return self.intent_map[intent]

        # 关键词匹配(简易模糊匹配)
        for key, value in self.intent_map.items():
            if key in intent or intent in key:
                self.logger.debug(f"模糊匹配意图 '{intent}' 到 '{key}'")
                return value

        return None