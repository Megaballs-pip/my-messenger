from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

port = int(os.environ.get("PORT", 10000))

with HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler) as httpd:
    print(f"✅ Веб-сервер запущен на порту {port}")
    httpd.serve_forever()
