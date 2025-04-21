import os
import sys
import subprocess
import argparse


def main():
    """运行Streamlit前端应用"""
    parser = argparse.ArgumentParser(description="启动AI Agent Streamlit前端")
    parser.add_argument("--port", type=int, default=8501, help="Streamlit服务端口")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000/api",
                        help="后端API基础URL")
    args = parser.parse_args()

    # 设置环境变量
    os.environ["API_BASE_URL"] = args.api_url

    # 获取脚本路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app_path = os.path.join(current_dir, "web", "streamlit_app.py")

    # 确保目录存在
    os.makedirs(os.path.dirname(streamlit_app_path), exist_ok=True)

    # 构建命令
    cmd = [
        "streamlit", "run",
        streamlit_app_path,
        "--server.port", str(args.port),
        "--browser.serverAddress", "localhost",
        "--server.headless", "true"
    ]

    print(f"启动Streamlit前端，访问 http://localhost:{args.port}")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n停止Streamlit服务")
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()