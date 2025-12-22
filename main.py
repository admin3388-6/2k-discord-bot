import discord
import os
from discord.ext import commands

# 1. جلب التوكن من متغيرات البيئة (التي وضعتها في Railway)
token = os.getenv('DISCORD_TOKEN')

# 2. تعريف الأذونات (Intents) - مهمة جداً لعمل البوت
intents = discord.Intents.default()
intents.message_content = True  # تفعيل قراءة الرسائل

# 3. تعريف متغير "bot" (هذا هو السطر الذي كان ينقصك)
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ تم تسجيل الدخول بنجاح كـ: {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

# 4. تشغيل البوت
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على متغير DISCORD_TOKEN في Railway!")
