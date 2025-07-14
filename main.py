from flask import Flask, request, jsonify, send_file
import os
import json
import csv
from datetime import datetime

app = Flask(__name__)
logs = []
LOG_FILE = "logs.json"

# 🟡 서버 시작 시 로그 복원
def load_logs():
    global logs
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            print(f"🔄 {len(logs)}개의 로그 복원 완료.")

# 🟢 로그 저장
def save_logs():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    print("💾 logs.json 저장 완료.")

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>ESP32 Log Server</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>ESP32 Log Server</h1>
        <p><a href="/log">로그 확인</a> | <a href="/log/json">JSON 로그</a> | <a href="/clear">로그 초기화</a></p>
    </body>
    </html>
    """

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
            save_logs()
            print(f"📥 Received: {log_entry}")
            return jsonify({"status": "ok", "message": "데이터 저장됨"}), 200
        else:
            return jsonify({"status": "error", "message": "빈 데이터입니다."}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/log', methods=['GET'])
def show_logs():
    if not logs:
        return "<html><body><h2>로그 없음</h2><p><a href='/'>홈으로</a></p></body></html>"

    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>ESP32 로그</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .log-entry {
                border: 1px solid #ddd;
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                background: #f9f9f9;
            }
            .timestamp {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 5px;
            }
            .data {
                background: #fff;
                padding: 8px;
                border-radius: 3px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <h2>ESP32 로그 (총 """ + str(len(logs)) + """개)</h2>
        <p>
            <a href='/'>홈으로</a> |
            <a href='/clear'>초기화</a> |
            <a href='/download/csv'>CSV 다운로드</a> |
            <a href='/download/txt'>TXT 다운로드</a>
        </p>
        <div>
    """

    for log in reversed(logs[-50:]):
        html += f"""
        <div class="log-entry">
            <div class="timestamp">{log['timestamp']}</div>
            <div class="data">{log['data']}</div>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """
    return html

@app.route('/log/json', methods=['GET'])
def show_logs_json():
    return jsonify(logs)

@app.route('/clear', methods=['GET', 'POST'])
def clear_logs():
    global logs
    logs = []
    save_logs()
    return "<html><body><h2>로그 초기화 완료</h2><p><a href='/'>홈으로</a></p></body></html>"

@app.route('/download/csv', methods=['GET'])
def download_csv():
    if not logs:
        return "로그 없음", 404

    csv_filename = "logs.csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Temperature', 'Humidity', 'Device', 'ESP_Timestamp'])

        for entry in logs:
            data = entry['data']
            writer.writerow([
                entry['timestamp'],
                data.get('temperature'),
                data.get('humidity'),
                data.get('device'),
                data.get('timestamp')
            ])

    return send_file(csv_filename, as_attachment=True)

@app.route('/download/txt', methods=['GET'])
def download_txt():
    if not logs:
        return "로그 없음", 404

    txt_filename = "logs.txt"
    with open(txt_filename, mode='w', encoding='utf-8') as file:
        for entry in logs:
            file.write(f"[{entry['timestamp']}] {json.dumps(entry['data'], ensure_ascii=False)}\n")

    return send_file(txt_filename, as_attachment=True)

@app.route('/status', methods=['GET'])
def server_status():
    return jsonify({
        "status": "running",
        "log_count": len(logs),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    load_logs()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
