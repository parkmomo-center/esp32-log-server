from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import pytz
import os
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logs = []

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>ESP32 WebSocket 로그</title>
        <meta charset="utf-8">
        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .log-entry {
                border: 1px solid #ccc;
                padding: 10px;
                margin-bottom: 8px;
                border-radius: 5px;
                background: #f9f9f9;
            }
        </style>
        <script>
            const socket = io("/ws");

            // 기존 로그 불러오기
            window.onload = async () => {
                const res = await fetch("/logs");
                const data = await res.json();
                const logArea = document.getElementById("logs");

                data.reverse().forEach((entry) => {
                    const div = document.createElement("div");
                    div.className = "log-entry";
                    div.innerText = entry.timestamp + " | " + JSON.stringify(entry.data);
                    logArea.appendChild(div);
                });
            };

            socket.on("connect", () => {
                console.log("WebSocket connected");
            });

            socket.on("message", function (data) {
                const logArea = document.getElementById("logs");
                const entry = document.createElement("div");
                entry.className = "log-entry";
                entry.innerText = data.timestamp + " | " + JSON.stringify(data.data);
                logArea.prepend(entry);
            });
        </script>
    </head>
    <body>
        <h2>ESP32 WebSocket 로그</h2>
        <p>
            <a href="/">홈으로</a> |
            <a href="/download/csv">CSV 다운로드</a> |
            <a href="/download/txt">TXT 다운로드</a> |
            <a href="/clear">로그 초기화</a>
        </p>
        <div id="logs"></div>
    </body>
    </html>
    """

# WebSocket 연결
@socketio.on('connect', namespace='/ws')
def ws_connect():
    print("WebSocket 연결됨")

# HTTP POST로 로그 수신
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if data:
            log_entry = {
                'timestamp': datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'),
                'data': data
            }
            logs.append(log_entry)

            # WebSocket으로 클라이언트에 푸시
            socketio.emit('message', log_entry, namespace='/ws')

            return jsonify({"status": "ok", "message": "데이터 저장됨"}), 200
        else:
            return jsonify({"status": "error", "message": "빈 데이터입니다."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 기존 로그 조회 API (새 탭에서 초기 출력용)
@app.route('/logs')
def get_logs():
    return jsonify(logs)

# 로그 초기화
@app.route('/clear', methods=['GET', 'POST'])
def clear_logs():
    global logs
    logs = []
    return """
    <html>
    <head><meta charset="utf-8"><title>초기화</title></head>
    <body>
        <h2>로그 초기화 완료</h2>
        <p><a href="/">홈으로</a></p>
    </body>
    </html>
    """

# CSV 다운로드
@app.route('/download/csv')
def download_csv():
    from io import StringIO
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['timestamp', 'temperature', 'humidity', 'device', 'raw_timestamp'])
    for log in logs:
        data = log['data']
        cw.writerow([
            log['timestamp'],
            data.get('temperature', ''),
            data.get('humidity', ''),
            data.get('device', ''),
            data.get('timestamp', '')
        ])
    output = si.getvalue()
    return (
        output,
        200,
        {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="esp32_logs.csv"'
        }
    )

# TXT 다운로드
@app.route('/download/txt')
def download_txt():
    content = ""
    for log in logs:
        content += f"{log['timestamp']} | {log['data']}\n"
    return (
        content,
        200,
        {
            'Content-Type': 'text/plain',
            'Content-Disposition': 'attachment; filename="esp32_logs.txt"'
        }
    )

# 서버 상태 확인 (Render ping 방지용)
@app.route('/status')
def server_status():
    return jsonify({
        'status': 'running',
        'log_count': len(logs),
        'timestamp': datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    })

# WebSocket 엔드포인트 설명
@app.route('/ws')
def ws_page():
    return "WebSocket endpoint"

# 실행
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
