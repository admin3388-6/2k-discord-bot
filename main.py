import discord
import os
import io
import requests
from discord.ext import commands
from discord import ui
from flask import Flask, jsonify, request
from flask_cors import CORS  # مكتبة حل مشكلة فشل الإرسال
from threading import Thread

# --- الإعدادات الثابتة ---
token = os.getenv('DISCORD_TOKEN')
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

# إعداد Flask مع السماح بطلبات الموقع (CORS)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

ticket_counter = 1

# --- نظام التذاكر ---
class CloseTicketModal(ui.Modal, title='سبب إغلاق التذكرة'):
    reason = ui.TextInput(label='لماذا تريد إغلاق التذكرة؟', style=discord.TextStyle.paragraph, min_length=5, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        log_ch = bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(title="📝 تقرير إغلاق تذكرة", description=f"بواسطة: {interaction.user.mention}\nالسبب: {self.reason.value}", color=0xff4757)
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
        super().__init__(placeholder="اختر نوع التذكرة للبدء...", options=options, custom_id="main_select")

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        t_type = self.values[0]
        t_names = {"report": "تبليغ", "problem": "مشكلة", "bug": "خطأ"}
        
        channel = await guild.create_text_channel(
            name=f"{t_names[t_type]}-{ticket_counter:04d}",
            category=category
        )
        ticket_counter += 1
        
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        for rid in STAFF_ROLES:
            role = guild.get_role(rid)
            if role: await channel.set_permissions(role, read_messages=True, send_messages=True)

        embed = discord.Embed(title=f"تذكرة {t_names[t_type]} جديدة", description="يرجى كتابة مشكلتك بالتفصيل هنا.\nسيتم الرد عليك من قبل الطاقم الإداري قريباً.", color=0x5865F2)
        embed.set_image(url="https://i.ibb.co/9HfG0Lz5/Picsart-25-12-25-15-08-29-765.jpg")
        await channel.send(content=f"{interaction.user.mention} | <@&1448639184532144128>", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {channel.mention}", ephemeral=True, delete_after=3)

class TicketMainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketTypeSelect())

@bot.event
async def on_ready():
    bot.add_view(TicketMainView())
    bot.add_view(TicketControlView())
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == IP_CHANNEL_ID:
        content = message.content.lower()
        if any(x in content for x in ["ip", "أي بي", "!ip", "اي بي"]):
            await message.reply(f"**IP Server:** `sd2k.progamer.me`")
    await bot.process_commands(message)

# --- نقطة النهاية للموقع (API) ---
@app.route('/setup_ticket', methods=['POST', 'OPTIONS'])
def setup_ticket_api():
    # معالجة طلبات Preflight للمتصفح
    if request.method == 'OPTIONS':
        return '', 204
    
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🎫 نظام التذاكر الموحد", description="للحصول على المساعدة، يرجى اختيار القسم المناسب من القائمة بالأسفل.\n\n⚠️ يمنع فتح التذاكر تافهة لضمان سرعة الرد.", color=0x2b2d31)
        embed.set_image(url="https://i.ibb.co/9HfG0Lz5/Picsart-25-12-25-15-08-29-765.jpg")
        
        bot.loop.create_task(channel.send(embed=embed, view=TicketMainView()))
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    bot.run(token)
