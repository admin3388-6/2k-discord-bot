import discord
import os
from discord.ext import commands
from flask import Flask, jsonify
from flask_cors import CORS  # مكتبة مهمة جداً لإصلاح مشكلة Offline
from threading import Thread

# --- إعدادات البوت ---
token = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True # لتفعيل الأوامر
bot = commands.Bot(command_prefix="!", intents=intents)

# --- إعدادات الويب ---
app = Flask(__name__)
CORS(app) # هذا السطر سيجعل صفحة الويب ترى البوت Online

@app.route('/stats')
def get_stats():
    return jsonify({
        "status": "Online",
        "server_count": len(bot.guilds),
        "user_count": sum(guild.member_count for guild in bot.guilds if guild.member_count)
    })

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    if token:
        bot.run(token)
