import sqlite3

def init_db():
    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def update_coins(user_id, coins):
    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    conn.close()

def get_top_100():
    conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 100")
    result = c.fetchall()
    conn.close()
    return result

