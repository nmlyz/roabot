# main.py
import discord
import os
from server import server_thread

# 環境変数から直接TOKENを取得
TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)