import asyncio
import websockets
import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

users = {}

def find_free_port():
    """Находит свободный порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

async def handler(ws):
    username = None
    try:
        msg = await ws.recv()
        data = json.loads(msg)
        if data["type"] == "register":
            username = data["username"]
            if username in users:
                await ws.send(json.dumps({"type": "error", "text": "Имя занято"}))
                return
            users[username] = ws
            await ws.send(json.dumps({"type": "users_list", "users": list(users.keys())}))
            await broadcast({"type": "info", "text": f"✨ {username} присоединился"})
            await broadcast_users_list()
        
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "public":
                await broadcast({"type": "public", "from": username, "text": data["text"], "time": datetime.now().strftime("%H:%M")})
            elif data["type"] == "private":
                target = data["to"]
                if target in users:
                    await users[target].send(json.dumps({"type": "private", "from": username, "text": data["text"], "time": datetime.now().strftime("%H:%M")}))
            elif data["type"] == "typing":
                target = data.get("to")
                if target and target in users:
                    await users[target].send(json.dumps({"type": "typing", "from": username}))
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if username and username in users:
            del users[username]
            await broadcast({"type": "info", "text": f"👋 {username} покинул чат"})
            await broadcast_users_list()

async def broadcast(msg):
    if users:
        await asyncio.wait([u.send(json.dumps(msg)) for u in users.values()])

async def broadcast_users_list():
    await broadcast({"type": "users_list", "users": list(users.keys())})

def start_http():
    """Запускает HTTP сервер для отдачи HTML"""
    port = find_free_port()
    print(f"📁 HTTP сервер на порту {port}")
    with HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

async def start_websocket():
    ws_port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handler, "0.0.0.0", ws_port):
        print(f"💬 WebSocket сервер на порту {ws_port}")
        await asyncio.Future()

if __name__ == "__main__":
    print("🚀 Запуск мессенджера...")
    # Запускаем HTTP сервер в фоне
    http_thread = threading.Thread(target=start_http, daemon=True)
    http_thread.start()
    # Запускаем WebSocket сервер
    asyncio.run(start_websocket())
