from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import hashlib
import hmac

app = Flask(__name__, static_folder='static')
CORS(app)

DATA_FILE = "users_data.json"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # Будем задавать в Railway

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Проверка подписи Telegram (безопасность)
def verify_telegram_auth(init_data):
    if not init_data:
        return None
    
    try:
        parsed = dict(x.split('=') for x in init_data.split('&') if '=' in x)
        hash_value = parsed.pop('hash', None)
        
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if check_hash == hash_value:
            return json.loads(parsed.get('user', '{}'))
    except:
        pass
    return None

@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/api/get_stats", methods=["POST"])
def get_stats():
    data = request.json
    user_id = str(data.get("user_id"))
    
    all_data = load_data()
    return jsonify(all_data.get(user_id, {
        "intellect": 0,
        "strength": 0,
        "health": 0,
        "achievements": [],
        "goals": []
    }))

@app.route("/api/save_stats", methods=["POST"])
def save_stats():
    data = request.json
    user_id = str(data.get("user_id"))
    user_data = data.get("data")
    
    all_data = load_data()
    all_data[user_id] = user_data
    save_data(all_data)
    
    return jsonify({"status": "ok"})

@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    all_data = load_data()
    users = []
    for uid, data in all_data.items():
        total = data.get("intellect", 0) + data.get("strength", 0) + data.get("health", 0)
        users.append({
            "total": total,
            "intellect": data.get("intellect", 0),
            "strength": data.get("strength", 0),
            "health": data.get("health", 0)
        })
    users.sort(key=lambda x: x["total"], reverse=True)
    return jsonify(users[:50])  # Топ-50

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))