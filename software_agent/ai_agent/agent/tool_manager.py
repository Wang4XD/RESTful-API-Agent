from typing import Dict, Any, List, Optional, Callable, Tuple

from ..config import BASE_CONFIG
from ..utils.logger import setup_logger
from ..api.api_client import APIClient
from ..api.endpoints import get_endpoint_url, API_ENDPOINTS


class Tool:
    """表示可执行的API工具"""

    def __init__(
            self,
            name: str,
            description: str,
            method: str,
            endpoint_action: str,
            required_params: List[str] = None,
            optional_params: List[str] = None,
            validation_func: Optional[Callable] = None
    ):
        self.name = name
        self.description = description
        self.method = method.upper()  # HTTP方法: GET, POST等
        self.endpoint_action = endpoint_action  # 在endpoints.py中定义的操作名
        self.required_params = required_params or []
        self.optional_params = optional_params or []
        self.validation_func = validation_func  # 自定义验证函数

    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证参数是否满足工具要求"""
        # 检查必需参数
        for param in self.required_params:
            if param not in params:
                return False, f"缺少必需参数: {param}"

        # 运行自定义验证(如果有)
        if self.validation_func:
            is_valid, error_msg = self.validation_func(params)
            if not is_valid:
                return False, error_msg

        return True, None


class ToolManager:
    """管理和执行API工具"""

    def __init__(self, api_client: APIClient = None):
        self.api_client = api_client or APIClient()
        self.logger = setup_logger("tool_manager", log_level=BASE_CONFIG["log_level"])
        self.tools = self._register_tools()

    def _register_tools(self) -> Dict[str, Tool]:
        """注册所有可用工具"""
        tools = {}

        # 用户管理工具
        tools["login"] = Tool(
            name="login",
            description="用户登录",
            method="POST",
            endpoint_action="login",
            required_params=["username", "password"]
        )

        tools["logout"] = Tool(
            name="logout",
            description="用户退出登录",
            method="POST",
            endpoint_action="logout"
        )

        tools["get_user"] = Tool(
            name="get_user",
            description="获取用户信息",
            method="GET",
            endpoint_action="get_user",
            required_params=["user_id"]
        )

        tools["create_user"] = Tool(
            name="create_user",
            description="创建新用户",
            method="POST",
            endpoint_action="create_user",
            required_params=["username", "email"],
            optional_params=["first_name", "last_name", "role"]
        )

        tools["update_user"] = Tool(
            name="update_user",
            description="更新用户信息",
            method="PUT",
            endpoint_action="update_user",
            required_params=["user_id"],
            optional_params=["email", "first_name", "last_name", "role"]
        )

        tools["delete_user"] = Tool(
            name="delete_user",
            description="删除用户",
            method="DELETE",
            endpoint_action="delete_user",
            required_params=["user_id"]
        )

        # 项目管理工具
        tools["list_projects"] = Tool(
            name="list_projects",
            description="列出所有项目",
            method="GET",
            endpoint_action="list_projects",
            optional_params=["page", "limit", "sort_by"]
        )

        tools["get_project"] = Tool(
            name="get_project",
            description="获取项目详情",
            method="GET",
            endpoint_action="get_project",
            required_params=["project_id"]
        )

        tools["create_project"] = Tool(
            name="create_project",
            description="创建新项目",
            method="POST",
            endpoint_action="create_project",
            required_params=["name"],
            optional_params=["description", "owner_id", "type", "tags"]
        )

        tools["update_project"] = Tool(
            name="update_project",
            description="更新项目信息",
            method="PUT",
            endpoint_action="update_project",
            required_params=["project_id"],
            optional_params=["name", "description", "owner_id", "type", "tags", "status"]
        )

        tools["delete_project"] = Tool(
            name="delete_project",
            description="删除项目",
            method="DELETE",
            endpoint_action="delete_project",
            required_params=["project_id"]
        )

        # 文件管理工具
        tools["list_files"] = Tool(
            name="list_files",
            description="列出项目文件",
            method="GET",
            endpoint_action="list_files",
            required_params=["project_id"],
            optional_params=["page", "limit", "type", "sort_by"]
        )

        tools["upload_file"] = Tool(
            name="upload_file",
            description="上传文件到项目",
            method="POST",
            endpoint_action="upload_file",
            required_params=["project_id", "file_data"],
            optional_params=["file_name", "file_type", "description"]
        )

        tools["download_file"] = Tool(
            name="download_file",
            description="下载项目文件",
            method="GET",
            endpoint_action="download_file",
            required_params=["project_id", "file_id"]
        )

        tools["delete_file"] = Tool(
            name="delete_file",
            description="删除项目文件",
            method="DELETE",
            endpoint_action="delete_file",
            required_params=["project_id", "file_id"]
        )

        # 数据处理工具
        tools["run_analysis"] = Tool(
            name="run_analysis",
            description="运行数据分析",
            method="POST",
            endpoint_action="run_analysis",
            required_params=["project_id", "analysis_type"],
            optional_params=["parameters", "input_file_ids", "options"]
        )

        tools["get_analysis_result"] = Tool(
            name="get_analysis_result",
            description="获取分析结果",
            method="GET",
            endpoint_action="get_analysis_result",
            required_params=["analysis_id"]
        )

        tools["export_report"] = Tool(
            name="export_report",
            description="导出分析报告",
            method="GET",
            endpoint_action="export_report",
            required_params=["report_id"],
            optional_params=["format", "include_charts"]
        )

        # 系统操作工具
        tools["get_system_status"] = Tool(
            name="get_system_status",
            description="获取系统状态",
            method="GET",
            endpoint_action="get_system_status"
        )

        tools["get_usage_statistics"] = Tool(
            name="get_usage_statistics",
            description="获取使用统计",
            method="GET",
            endpoint_action="get_usage_statistics",
            optional_params=["start_date", "end_date", "user_id", "project_id"]
        )

        return tools

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取指定名称的工具"""
        return self.tools.get(tool_name)

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            self.logger.error(f"未找到工具: {tool_name}")
            return {"success": False, "error": f"未找到工具: {tool_name}"}

        # 验证参数
        is_valid, error_msg = tool.validate_params(params)
        if not is_valid:
            self.logger.error(f"工具参数验证失败: {error_msg}")
            return {"success": False, "error": error_msg}

        # 准备API调用
        try:
            # 获取API端点
            endpoint_params = {key: value for key, value in params.items()
                               if
                               key in tool.required_params and "{" + key + "}" in API_ENDPOINTS[tool.endpoint_action]}

            endpoint = get_endpoint_url(tool.endpoint_action, **endpoint_params)

            # 准备API参数(排除路径参数)
            api_params = {}
            api_data = {}

            # 处理GET、DELETE的查询参数
            if tool.method in ["GET", "DELETE"]:
                # 对于GET和DELETE请求，所有参数作为查询参数
                api_params = {key: value for key, value in params.items()
                              if key not in endpoint_params}  # 排除已在路径中使用的参数
            else:
                # 对于POST、PUT、PATCH请求，参数作为请求体
                api_data = {key: value for key, value in params.items()
                            if key not in endpoint_params}  # 排除已在路径中使用的参数

            # 执行API调用
            self.logger.info(f"执行工具: {tool_name}, 方法: {tool.method}, 端点: {endpoint}")

            if tool.method == "GET":
                response = self.api_client.get(endpoint, params=api_params)
            elif tool.method == "POST":
                response = self.api_client.post(endpoint, data=api_data, params=api_params)
            elif tool.method == "PUT":
                response = self.api_client.put(endpoint, data=api_data, params=api_params)
            elif tool.method == "DELETE":
                response = self.api_client.delete(endpoint, params=api_params)
            elif tool.method == "PATCH":
                response = self.api_client.patch(endpoint, data=api_data, params=api_params)
            else:
                return {"success": False, "error": f"不支持的HTTP方法: {tool.method}"}

            # 检查响应
            if "error" in response:
                self.logger.error(f"工具执行失败: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error"),
                    "details": response.get("details", {})
                }

            return {
                "success": True,
                "tool": tool_name,
                "result": response
            }

        except Exception as e:
            self.logger.error(f"工具执行异常: {str(e)}")
            return {"success": False, "error": f"工具执行异常: {str(e)}"}