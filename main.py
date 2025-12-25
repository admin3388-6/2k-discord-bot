import discord
import os
import io
import requests
from discord.ext import commands
from discord import ui
from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
from PIL import Image, ImageDraw, ImageOps

# --- الإعدادات الثابتة (تعديل الروابط والـ IDs هنا) ---
token = os.getenv('DISCORD_TOKEN')
WELCOME_BG_URL = "https://i.ibb.co/m5m8Z8Y/welcome-bg.jpg" # رابط صورتك الثابتة
RULES_CHANNEL_ID = 1448638848513871872
TICKET_CHANNEL_ID = 1448638848803405846
LOG_CHANNEL_ID = 1449057792739508425
CATEGORY_ID = 1453747983530070126
IP_CHANNEL_ID = 1448805638686769213

STAFF_ROLES = [1448639184532144128, 1448638848098631881, 1448638848090509381, 
               1448638848090509380, 1448638848090509379, 1449055160944033934]

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
CORS(app)

welcome_config = {"channel_id": None}
ticket_counter = 1

# --- أنظمة التذاكر ---
class CloseTicketModal(ui.Modal, title='سبب إغلاق التذكرة'):
    reason = ui.TextInput(label='السبب', style=discord.TextStyle.paragraph, min_length=5, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        log_ch = bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(title="📝 تقرير إغلاق", description=f"بواسطة: {interaction.user.mention}\nالسبب: {self.reason.value}", color=0xff0000)
        if log_ch: await log_ch.send(embed=embed)
        await interaction.channel.delete()

class TicketControlView(ui.View):
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(CloseTicketModal())

class TicketTypeSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="تبليغ عن شخص", value="report", emoji="⚖️"),
            discord.SelectOption(label="مشكلة", value="problem", emoji="🛠️"),
            discord.SelectOption(label="خطأ Bug", value="bug", emoji="👾")
        ]
        super().__init__(placeholder="اختر نوع التكت...", options=options, custom_id="main_select")

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        t_type = self.values[0]
        t_names = {"report": "تبليغ", "problem": "مشكلة", "bug": "خطأ"}
        channel = await guild.create_text_channel(name=f"{t_names[t_type]}-{ticket_counter:04d}", category=category)
        ticket_counter += 1
        
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        for rid in STAFF_ROLES:
            role = guild.get_role(rid)
            if role: await channel.set_permissions(role, read_messages=True, send_messages=True)

        embed = discord.Embed(title=f"تذكرة {t_names[t_type]}", description="انتظر الرد الإداري.", color=0x5865F2)
        embed.set_image(url="https://i.ibb.co/9HfG0Lz5/Picsart-25-12-25-15-08-29-765.jpg")
        await channel.send(content=f"{interaction.user.mention} | الإدارة", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ تم فتح التكت: {channel.mention}", ephemeral=True, delete_after=3)

class TicketMainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

# --- أحداث البوت ---
@bot.event
async def on_ready():
    bot.add_view(TicketMainView())
    bot.add_view(TicketControlView())
    print(f"Bot {bot.user} is online!")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == IP_CHANNEL_ID:
        if any(x in message.content.lower() for x in ["ip", "أي بي", "!ip", "اي بي"]):
            await message.reply(f"**IP Server:** `sd2k.progamer.me`")
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if not welcome_config["channel_id"]: return
    channel = bot.get_channel(int(welcome_config["channel_id"]))
    try:
        bg_res = requests.get(WELCOME_BG_URL)
        bg = Image.open(io.BytesIO(bg_res.content)).convert("RGBA")
        pfp_res = requests.get(member.display_avatar.url)
        pfp = Image.open(io.BytesIO(pfp_res.content)).convert("RGBA")
        pfp = pfp.resize((271, 271), Image.LANCZOS)
        mask = Image.new('L', (271, 271), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 271, 271), fill=255)
        pfp.putalpha(mask)
        bg.paste(pfp, (627, 196), pfp) # إحداثياتك 2K
        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            await channel.send(f"مرحبا بك {member.mention}", file=discord.File(out, "welcome.png"))
    except: pass

# --- واجهة الـ API للموقع ---
@app.route('/get_channels')
def get_ch():
    return jsonify([{"id": str(c.id), "name": c.name} for g in bot.guilds for c in g.text_channels])

@app.route('/setup_ticket', methods=['POST'])
def setup_tkt():
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    embed = discord.Embed(title="🎫 نظام التذاكر", description="اختر القسم المناسب لفتح تذكرة جديدة.", color=0x2b2d31)
    embed.set_image(url="https://i.ibb.co/9HfG0Lz5/Picsart-25-12-25-15-08-29-765.jpg")
    bot.loop.create_task(channel.send(embed=embed, view=TicketMainView()))
    return jsonify({"status": "ok"})

@app.route('/send_embed', methods=['POST'])
def send_emb():
    data = request.json
    channel = bot.get_channel(int(data['channel_id']))
    embed = discord.Embed(title=data['title'], description=data['description'], color=int(data['color'].lstrip('#'), 16))
    bot.loop.create_task(channel.send(embed=embed))
    return jsonify({"status": "ok"})

@app.route('/send_normal_msg', methods=['POST'])
def send_norm():
    data = request.json
    channel = bot.get_channel(int(data['channel_id']))
    bot.loop.create_task(channel.send(data['message']))
    return jsonify({"status": "ok"})

@app.route('/save_welcome', methods=['POST'])
def save_wel():
    welcome_config.update(request.json)
    return jsonify({"status": "ok"})

def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()
bot.run(token)
