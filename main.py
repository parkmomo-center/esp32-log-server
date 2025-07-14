from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
logs = []

def get_kst_time():
    return (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ESP32 WebSocket 로그</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .log-entry { margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; background: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>ESP32 WebSocket 로그</h2>
        <div id="log-container"></div>

        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        <script>
            const socket = io();
            const container = document.getElementById('log-container');

            socket.on('new_log', function (log) {
                const div = document.createElement('div');
                div.className = 'log-entry';
                div.textContent = `${log.timestamp} | ${JSON.stringify(log.data)}`;
                container.prepend(div);  // 최신 로그 맨 위
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if data:
            log_entry = {
                'timestamp': get_kst_time(),
                'data': data
            }
            logs.append(log_entry)

            print(f"Received: {log_entry}")
            socketio.emit('new_log', log_entry)  # WebSocket으로 전송

            return jsonify({"status": "ok", "message": "저장 및 전송 완료"}), 200
        else:
            return jsonify({"status": "error", "message": "빈 데이터입니다."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def on_connect():
    print("WebSocket 클라이언트 연결됨")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
