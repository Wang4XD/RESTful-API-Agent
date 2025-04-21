import argparse
import os
import sys
import uvicorn
from typing import Dict, Any

from .config import WEB_CONFIG, BASE_CONFIG
from .utils.logger import setup_logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI Agent服务")
    parser.add_argument("--host", type=str, default=WEB_CONFIG["host"], help="服务主机地址")
    parser.add_argument("--port", type=int, default=WEB_CONFIG["port"], help="服务端口")
    parser.add_argument("--debug", action="store_true", default=BASE_CONFIG["debug"], help="启用调试模式")
    parser.add_argument("--log-level", type=str, default=BASE_CONFIG["log_level"],
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="日志级别")
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    logger = setup_logger(
        "main",
        log_level=args.log_level,
        log_file="logs/ai_agent.log"
    )

    logger.info(f"启动AI Agent服务，版本 {BASE_CONFIG['version']}")
    logger.info(f"主机: {args.host}, 端口: {args.port}, 调试模式: {args.debug}")

    try:
        # 启动web应用
        uvicorn.run(
            "ai_agent.web.app:app",
            host=args.host,
            port=args.port,
            reload=args.debug,
            log_level=args.log_level.lower()
        )
    except Exception as e:
        logger.error(f"启动服务失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()