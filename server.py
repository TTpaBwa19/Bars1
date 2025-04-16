from flask import Flask, jsonify, request
import mysql.connector
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Конфигурация базы данных (используем переменные окружения, если есть)
db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root"),
    "database": os.environ.get("DB_NAME", "barsiq")
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к базе данных: {err}")
        return None

@app.route('/get_user_data', methods=['GET'])
def get_user_data():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            return jsonify({
                "success": True,
                "user": {
                    "user_id": user_data['user_id'],
                    "username": user_data['username'],
                    "coins": user_data['coins'],
                    "last_update": user_data['last_update'].isoformat() if user_data['last_update'] else None
                }
            })
        else:
            return jsonify({
                "success": True,
                "user": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_user_data', methods=['POST'])
def update_user_data():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        now = datetime.now()
        
        cursor.execute("SELECT coins, last_update FROM users WHERE user_id = %s", (data['user_id'],))
        existing = cursor.fetchone()
        
        if existing and 'last_update' in data:
            server_last_update = existing[1]
            client_last_update = datetime.fromisoformat(data['last_update'])
            if server_last_update > client_last_update:
                return jsonify({
                    "success": True,
                    "updated": False,
                    "message": "Server data is newer"
                })

        cursor.execute("""
            INSERT INTO users (user_id, username, coins, last_update)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = COALESCE(VALUES(username), username),
                coins = VALUES(coins),
                last_update = VALUES(last_update)
        """, (
            data['user_id'],
            data.get('username'),
            data.get('coins', 0),
            now
        ))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "updated": True,
            "last_update": now.isoformat()
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, username, coins 
            FROM users 
            ORDER BY coins DESC 
            LIMIT 100
        """)
        leaderboard = cursor.fetchall()
        return jsonify({
            "success": True,
            "leaderboard": leaderboard
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Создаём таблицу при первом запуске
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(255) PRIMARY KEY,
                    username VARCHAR(255),
                    coins INT DEFAULT 0,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
