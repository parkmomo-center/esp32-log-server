from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)
logs = []

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>ESP32 Log Server</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            .nav { margin: 20px 0; }
            .nav a { margin-right: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .nav a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ESP32 Log Server</h1>
                <p>서버가 정상적으로 실행 중입니다.</p>
            </div>
            <div class="nav">
                <a href="/log">로그 확인</a>
                <a href="/log/json">JSON 로그</a>
                <a href="/clear">로그 초기화</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if data:
            # 타임스탬프 추가
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data': data
            }
            logs.append(log_entry)
            print(f"Received: {log_entry}")
            return jsonify({"status": "ok", "message": "데이터가 성공적으로 저장되었습니다."}), 200
        else:
            return jsonify({"status": "error", "message": "빈 데이터입니다."}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/log', methods=['GET'])
def show_logs():
    if not logs:
        return """
        <html>
        <head>
            <title>로그 확인</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="5">
        </head>
        <body>
            <h2>ESP32 로그</h2>
            <p>로그 파일이 존재하지 않습니다.</p>
            <p><a href="/">홈으로 돌아가기</a></p>
        </body>
        </html>
        """
    
    html_content = """
    <html>
    <head>
        <title>ESP32 로그</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="5">
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
        <p><a href="/">홈으로</a> | <a href="/clear">로그 초기화</a></p>
        <div>
    """
    
    # 최신 로그부터 보여주기
    for log in reversed(logs[-50:]):  # 최신 50개만 표시
        html_content += f"""
        <div class="log-entry">
            <div class="timestamp">{log['timestamp']}</div>
            <div class="data">{log['data']}</div>
        </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return html_content

@app.route('/log/json', methods=['GET'])
def show_logs_json():
    return jsonify(logs)

@app.route('/clear', methods=['GET', 'POST'])
def clear_logs():
    global logs
    logs = []
    return """
    <html>
    <head>
        <title>로그 초기화</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h2>로그가 초기화되었습니다.</h2>
        <p><a href="/">홈으로 돌아가기</a></p>
    </body>
    </html>
    """

@app.route('/status', methods=['GET'])
def server_status():
    return jsonify({
        "status": "running",
        "log_count": len(logs),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
