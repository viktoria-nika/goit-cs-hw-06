import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import threading
from urllib.parse import urlparse, parse_qs
import time
from datetime import datetime
import pymongo

# Підключення до MongoDB
client = pymongo.MongoClient("mongodb://mongo:27017/")
db = client['messages_db']
collection = db['messages']

# Маршрутизація
class MyHandler(BaseHTTPRequestHandler):

    def _send_response(self, content_type, body):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path == "/":
            with open("index.html", "r") as f:
                content = f.read()
            self._send_response('text/html', content)

        elif self.path == "/message":
            with open("message.html", "r") as f:
                content = f.read()
            self._send_response('text/html', content)

        elif self.path == "/style.css":
            with open("style.css", "r") as f:
                content = f.read()
            self._send_response('text/css', content)

        elif self.path == "/logo.png":
            with open("logo.png", "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(content)

        else:
            with open("error.html", "r") as f:
                content = f.read()
            self._send_response('text/html', content)

    def do_POST(self):
        if self.path == "/send_message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message_data = parse_qs(post_data.decode('utf-8'))

            username = message_data.get("username", [""])[0]
            message = message_data.get("message", [""])[0]

            if username and message:
                # Відправка даних на сокет сервер
                send_message_to_socket(username, message)
                self.send_response(302)
                self.send_header('Location', '/message')
                self.end_headers()

def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting HTTP server on port 3000...')
    httpd.serve_forever()

# Крок 2: Реалізація Socket-сервера
def send_message_to_socket(username, message):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 5000))  # Підключення до сокет-сервера
    message_data = {
        "username": username,
        "message": message,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    }
    client_socket.sendall(json.dumps(message_data).encode())
    client_socket.close()

def run_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5000))
    server_socket.listen(5)
    print('Socket server running on port 5000...')

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(1024)
        if data:
            message_data = json.loads(data.decode())
            collection.insert_one(message_data)
            print(f"Message saved: {message_data}")
        client_socket.close()

# Запуск серверів в окремих потоках
if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=run_socket_server, daemon=True).start()
    while True:
        time.sleep(1)