"""
局域网 / 隧道预览用的反向代理：
- 根路径：直接吐 H5 构建产物（en-study-web/dist）
- /api、/tts、/health、/admin：转发到本机后端 127.0.0.1:8000

这样通过 cloudflared 之类的 https 隧道访问时，H5 和接口同源，
手机上才能拿到“安全上下文”，麦克风/录音才可用。
"""
import http.server
import os
import socketserver
import sys
import urllib.request
import urllib.error

DIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "en-study-web", "dist"
)
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 10200
BACKEND = "http://127.0.0.1:8000"
PROXY_PREFIXES = ("/api/", "/tts", "/health", "/admin", "/docs", "/openapi.json")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST, **kwargs)

    def log_message(self, fmt, *args):  # 少打日志
        pass

    def _proxy(self, method):
        url = BACKEND + self.path
        body = None
        if method in ("POST", "PUT", "PATCH"):
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
        req = urllib.request.Request(url, data=body, method=method)
        for k, v in self.headers.items():
            if k.lower() in ("host", "connection", "content-length"):
                continue
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in ("transfer-encoding", "connection", "content-length"):
                        continue
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read()
            self.send_response(e.code)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:  # noqa
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy("POST")
        self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy("DELETE")
        self.send_error(404)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    os.chdir(DIST)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"serving {DIST} on :{PORT}, api -> {BACKEND}", flush=True)
        httpd.serve_forever()
