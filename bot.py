import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7810631158:AAFZnfH_Y1Bfai_pJ-SyWshFwyKZICf-w18"
WEB_APP_URL = "https://ttpabwa19.github.io/Bars/"  # Заменить на актуальную ссылку

# Подключение к базе
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 0
    )
''')
conn.commit()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    await message.answer(
        "🎮 BarsIQ - мини-игра для прокачки мозга!\nНажми кнопку ниже, чтобы начать:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🧠 Играть в BarsIQ", web_app=types.WebAppInfo(url=WEB_APP_URL))
        )
    )

# Обработка web_app_data
@dp.message_handler(content_types=['web_app_data'])
async def web_app_data_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        data = json.loads(message.web_app_data.data)

        if data.get("action") == "click":
            coins = int(data.get("coins", 0))
            cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (coins, user_id))
            conn.commit()
            await message.answer(f"✅ Монеты обновлены: {coins} 💰")

        elif data.get("action") == "get_leaderboard":
            cursor.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 100")
            top_users = cursor.fetchall()

            leaderboard = [{"user_id": uid, "coins": c} for uid, c in top_users]
            await message.answer_web_app(json.dumps({"leaderboard": leaderboard}))

    except Exception as e:
        await message.answer("⚠️ Ошибка при обработке данных!")
        logger.error(f"Ошибка при обработке web_app_data: {e}")

if __name__ == '__main__':
    logger.info("Бот запущен")
    executor.start_polling(dp)







