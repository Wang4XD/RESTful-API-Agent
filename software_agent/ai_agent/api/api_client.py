import requests
import time
import json
from typing import Dict, Any, Optional, Union
from ..utils.logger import setup_logger
from ..config import API_CONFIG, BASE_CONFIG


class APIClient:
    """与软件RESTful API交互的客户端"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or API_CONFIG
        self.base_url = self.config["base_url"]
        self.api_key = self.config["api_key"]
        self.timeout = self.config["timeout"]
        self.retry_attempts = self.config["retry_attempts"]
        self.retry_delay = self.config["retry_delay"]
        self.logger = setup_logger("api_client", log_level=BASE_CONFIG["log_level"])
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _make_url(self, endpoint: str) -> str:
        """构建完整的URL"""
        if endpoint.startswith("http"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self.base_url}{endpoint}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理API响应"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP错误: {str(e)}")
            error_detail = {}
            try:
                error_detail = response.json()
            except:
                error_detail = {"status_code": response.status_code, "text": response.text}

            return {"error": str(e), "details": error_detail}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求错误: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            self.logger.error("JSON解析错误")
            return {"error": "无法解析响应JSON", "text": response.text}

    def request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
            retry_count: int = 0
    ) -> Dict[str, Any]:
        """发送API请求并返回结果"""
        url = self._make_url(endpoint)
        request_headers = headers or {}

        try:
            self.logger.debug(f"发送{method}请求到{url}")
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            if retry_count < self.retry_attempts:
                self.logger.warning(f"请求超时，尝试重试({retry_count + 1}/{self.retry_attempts})")
                time.sleep(self.retry_delay)
                return self.request(method, endpoint, params, data, headers, retry_count + 1)
            else:
                self.logger.error("请求超时，已达到最大重试次数")
                return {"error": "请求超时"}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求异常: {str(e)}")
            return {"error": str(e)}

    # 便捷方法
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> \
    Dict[str, Any]:
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("POST", endpoint, params=params, data=data, headers=headers)

    def put(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("PUT", endpoint, params=params, data=data, headers=headers)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("DELETE", endpoint, params=params, headers=headers)

    def patch(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None,
              headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.request("PATCH", endpoint, params=params, data=data, headers=headers)