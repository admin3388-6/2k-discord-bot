import discord
import os
import io
import requests
from discord.ext import commands
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
from PIL import Image, ImageDraw, ImageOps

# --- الإعدادات ---
token = os.getenv('DISCORD_TOKEN')
RULES_CHANNEL_ID = 1448638848513871872

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
CORS(app)

# إعدادات الترحيب الافتراضية
welcome_config = {
    "channel_id": None,
    "x": 433,
    "y": 235,
    "bg_url": "https://i.ibb.co/m5m8Z8Y/welcome-bg.jpg" # رابط الصورة الافتراضي
}

@app.route('/get_channels')
def get_channels():
    channels = [{"id": str(c.id), "name": f"{c.guild.name} | #{c.name}"} 
                for g in bot.guilds for c in g.text_channels]
    return jsonify(channels)

@app.route('/save_welcome_settings', methods=['POST'])
def save_settings():
    global welcome_config
    data = request.json
    welcome_config.update(data)
    welcome_config["channel_id"] = int(data['channel_id'])
    return jsonify({"status": "success"})

@bot.event
async def on_member_join(member):
    if not welcome_config["channel_id"]: return
    
    channel = bot.get_channel(welcome_config["channel_id"])
    if not channel: return

    try:
        # جلب خلفية الترحيب
        bg_res = requests.get(welcome_config["bg_url"])
        bg = Image.open(io.BytesIO(bg_res.content)).convert("RGBA")
        
        # جلب صورة البروفايل
        pfp_res = requests.get(member.display_avatar.url)
        pfp = Image.open(io.BytesIO(pfp_res.content)).convert("RGBA")
        
        # جعل البروفايل دائري
        size = (210, 210) 
        pfp = pfp.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        pfp_circle = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
        pfp_circle.putalpha(mask)

        # دمج الصور بناءً على إحداثيات الموقع
        bg.paste(pfp_circle, (int(welcome_config['x']), int(welcome_config['y'])), pfp_circle)

        with io.BytesIO() as img_bin:
            bg.save(img_bin, 'PNG')
            img_bin.seek(0)
            text = f"مرحبا بك {member.mention}\nشكرا لانضمامك لـ **{member.guild.name}**\nعددنا الآن: **{member.guild.member_count}**\nقوانيننا: <#{RULES_CHANNEL_ID}>"
            await channel.send(text, file=discord.File(fp=img_bin, filename='welcome.png'))
    except Exception as e:
        print(f"Error: {e}")

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(token)
