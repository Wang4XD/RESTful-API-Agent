from typing import Dict, Any, List, Optional

# 这是示例API操作，实际部署时应替换为你公司软件的API
API_ENDPOINTS = {
    # 用户管理
    "login": "/auth/login",
    "logout": "/auth/logout",
    "get_user": "/users/{user_id}",
    "create_user": "/users",
    "update_user": "/users/{user_id}",
    "delete_user": "/users/{user_id}",

    # 项目管理
    "list_projects": "/projects",
    "get_project": "/projects/{project_id}",
    "create_project": "/projects",
    "update_project": "/projects/{project_id}",
    "delete_project": "/projects/{project_id}",

    # 文件管理
    "list_files": "/projects/{project_id}/files",
    "upload_file": "/projects/{project_id}/files",
    "download_file": "/projects/{project_id}/files/{file_id}",
    "delete_file": "/projects/{project_id}/files/{file_id}",

    # 数据处理
    "run_analysis": "/analysis",
    "get_analysis_result": "/analysis/{analysis_id}",
    "export_report": "/reports/{report_id}/export",

    # 系统操作
    "get_system_status": "/system/status",
    "get_usage_statistics": "/system/statistics",
}


def get_endpoint_url(action_name: str, **kwargs) -> str:
    """
    根据操作名获取API端点URL，并填充路径参数

    Args:
        action_name: API操作名称
        kwargs: 路径参数值

    Returns:
        格式化后的端点URL
    """
    if action_name not in API_ENDPOINTS:
        raise ValueError(f"未知的API操作: {action_name}")

    endpoint = API_ENDPOINTS[action_name]

    # 替换路径参数
    for key, value in kwargs.items():
        placeholder = "{" + key + "}"
        if placeholder in endpoint:
            endpoint = endpoint.replace(placeholder, str(value))

    return endpoint