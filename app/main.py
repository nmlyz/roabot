import discord
import os
from server import server_thread
from datetime import datetime
import pytz  # 日本時間用

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # 日本時間に変換
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    
    print('='*50)
    print(f'[{current_time}] BOTが起動しました！')
    print(f'BOT名: {client.user.name}')
    print(f'BOT ID: {client.user.id}')
    print(f'Discord.py バージョン: {discord.__version__}')
    print('='*50)
    
    # デプロイ通知をDiscordチャンネルに送信
    for guild in client.guilds:
        for channel in guild.text_channels:
            # 一般チャンネルまたはbotチャンネルを探す
            if channel.name in ['一般', 'general', 'bot', 'bot-log']:
                try:
                    await channel.send(f'🚀 BOTが再起動されました！\n⏰ 起動時刻: {current_time}')
                    break  # 1つのサーバーにつき1回だけ通知
                except:
                    continue

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$'):
        command = message.content.lower()
        
        if command == '$hello':
            await message.channel.send('Hello!')
        
        elif command == '$help':
            help_text = """
**使用可能なコマンド一覧:**
`$hello` - BOTが挨拶を返します
`$help` - このヘルプメッセージを表示します
`$status` - BOTの稼働状況を表示します
"""
            await message.channel.send(help_text)
            
        elif command == '$status':
            # 日本時間で現在時刻を取得
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
            
            status_text = f"""
**BOTステータス**
🤖 BOT名: {client.user.name}
⚡ 接続状態: オンライン
⏰ 現在時刻: {current_time}
🏓 Pingレイテンシー: {round(client.latency * 1000)}ms
"""
            await message.channel.send(status_text)

# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)