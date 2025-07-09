from flask import Flask, request, jsonify
import os

app = Flask(__name__)
logs = []

@app.route('/')
def home():
    return "ESP32 Log Server is Running"

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    logs.append(data)
    print(f"Received: {data}")
    return jsonify({"status": "ok"}), 200

@app.route('/log', methods=['GET'])
def show_logs():
    if not logs:
        return "로그 파일이 존재하지 않습니다."
    return "<br>".join([str(log) for log in logs])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
