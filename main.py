from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logs = []

# 기본 홈 화면
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>ESP32 WebSocket 로그</title>
        <meta charset="utf-8">
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
            var socket = new WebSocket("wss://" + location.host + "/ws");

            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const logArea = document.getElementById("logs");
                const entry = document.createElement("div");
                entry.className = "log-entry";
                entry.innerText = data.timestamp + " | " + JSON.stringify(data.data);
                logArea.prepend(entry);
            };
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
        <div id="logs">
        </div>
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
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data': data
            }
            logs.append(log_entry)

            # WebSocket으로 브라우저에 전송
            socketio.emit('message', log_entry, namespace='/ws')
            return jsonify({"status": "ok", "message": "데이터 저장됨"}), 200
        else:
            return jsonify({"status": "error", "message": "빈 데이터입니다."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

# 상태 확인용 API
@app.route('/status')
def server_status():
    return jsonify({
        'status': 'running',
        'log_count': len(logs),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# WebSocket 핸들러 (텍스트용, 브라우저 직접 연결 시 사용 가능)
@app.route('/ws')
def ws_page():
    return "WebSocket endpoint"

# 실행
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
