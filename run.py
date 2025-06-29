# 创建应用实例
import sys

from wxcloudrun import app

# 启动Flask Web服务
if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    print(f"Starting server on {host}:{port}")
    app.run(host=host, port=port)
