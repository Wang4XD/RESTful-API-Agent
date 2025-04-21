from typing import Dict, Any, Tuple, Optional
import re
import json


def validate_email(email: str) -> bool:
    """验证电子邮件格式"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_project_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """验证项目参数"""
    # 名称长度验证
    if "name" in params and (len(params["name"]) < 3 or len(params["name"]) > 100):
        return False, "项目名称长度必须在3-100个字符之间"

    # 标签格式验证
    if "tags" in params:
        tags = params["tags"]
        if not isinstance(tags, list):
            try:
                # 尝试转换字符串为列表
                if isinstance(tags, str):
                    json.loads(tags)
            except json.JSONDecodeError:
                return False, "标签必须是有效的列表或JSON字符串"

    return True, None


def validate_analysis_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """验证分析参数"""
    # 验证分析类型
    valid_types = ["statistical", "predictive", "descriptive", "diagnostic", "prescriptive"]
    if "analysis_type" in params and params["analysis_type"] not in valid_types:
        return False, f"分析类型必须是以下之一: {', '.join(valid_types)}"

    # 验证参数格式
    if "parameters" in params:
        parameters = params["parameters"]
        if not isinstance(parameters, dict):
            try:
                # 尝试转换字符串为字典
                if isinstance(parameters, str):
                    json.loads(parameters)
            except json.JSONDecodeError:
                return False, "参数必须是有效的对象或JSON字符串"

    return True, None


def validate_date_format(date_str: str) -> bool:
    """验证日期格式 (YYYY-MM-DD)"""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))


def validate_statistics_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """验证统计参数"""
    # 验证日期格式
    if "start_date" in params and not validate_date_format(params["start_date"]):
        return False, "开始日期格式无效，应为YYYY-MM-DD"

    if "end_date" in params and not validate_date_format(params["end_date"]):
        return False, "结束日期格式无效，应为YYYY-MM-DD"

    # 验证日期范围
    if "start_date" in params and "end_date" in params:
        if params["start_date"] > params["end_date"]:
            return False, "开始日期不能晚于结束日期"

    return True, None