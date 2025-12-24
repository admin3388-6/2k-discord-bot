import discord
import os
from discord.ext import commands
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread

# --- إعدادات البوت ---
token = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# --- إعدادات الويب (API) ---
app = Flask(__name__)
CORS(app)

@app.route('/stats')
def get_stats():
    return jsonify({
        "status": "Online",
        "server_count": len(bot.guilds),
        "user_count": sum(guild.member_count for guild in bot.guilds if guild.member_count)
    })

@app.route('/send_embed', methods=['POST'])
def send_embed():
    data = request.json
    try:
        channel_id = data.get('channel_id')
        title = data.get('title')
        description = data.get('description')
        color_hex = data.get('color', '#5865F2').lstrip('#')
        image_url = data.get('image_url')

        channel = bot.get_channel(int(channel_id))
        if not channel:
            return jsonify({"status": "error", "message": "Channel not found"}), 404

        # بناء الإيمباد الاحترافي
        embed = discord.Embed(
            title=title, 
            description=description, 
            color=int(color_hex, 16)
        )
        if image_url:
            embed.set_image(url=image_url)
        
        embed.set_footer(text="Sky Data Systems • Powered by Railway", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        
        # إرسال المهمة للبوت
        bot.loop.create_task(channel.send(embed=embed))
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    if token:
        bot.run(token)
