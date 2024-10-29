import discord
import os
from server import server_thread
from datetime import datetime
import pytz

TOKEN = os.environ["TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    
    print('='*50)
    print(f'[{current_time}] BOTが起動しました！')
    print(f'BOT名: {client.user.name}')
    print(f'BOT ID: {client.user.id}')
    print(f'Admin ID: {ADMIN_USER_ID}')
    print(f'Discord.py バージョン: {discord.__version__}')
    print('='*50)
    
    try:
        admin_user = await client.fetch_user(ADMIN_USER_ID)
        await admin_user.send(f'🚀 BOTが再起動されました！\n⏰ 起動時刻: {current_time}')
    except:
        print("管理者への通知送信に失敗しました")
    
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name in ['一般', 'general', 'bot', 'bot-log']:
                try:
                    await channel.send(f'🚀 BOTが再起動されました！\n⏰ 起動時刻: {current_time}')
                    break
                except:
                    continue

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$'):
        command = message.content.lower()
        
        if message.author.id == ADMIN_USER_ID:
            if command == '$shutdown':
                await message.channel.send('⚠️ BOTをシャットダウンします...')
                await client.close()
                return
        
        if command == '$hello':
            await message.channel.send('Hello!')
        
        elif command == '$help':
            help_text = """
**使用可能なコマンド一覧:**
`$hello` - BOTが挨拶を返します
`$help` - このヘルプメッセージを表示します
`$status` - BOTの動作状況を表示します
"""
            if message.author.id == ADMIN_USER_ID:
                help_text += "\n**管理者用コマンド:**\n`$shutdown` - BOTをシャットダウンします"
            
            await message.channel.send(help_text)
            
        elif command == '$status':
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
            
            # 応答速度を計算（ミリ秒単位）
            response_time = round(client.latency * 1000)
            
            # 応答速度の評価
            if response_time < 100:
                speed_status = "とても良好"
            elif response_time < 200:
                speed_status = "良好"
            elif response_time < 500:
                speed_status = "普通"
            else:
                speed_status = "やや遅い"
            
            status_text = f"""
**BOTの状態**
🤖 BOT名: {client.user.name}
⚡ 接続状態: オンライン
⏰ 現在時刻: {current_time}
📶 応答速度: {response_time}ミリ秒 ({speed_status})
"""
            await message.channel.send(status_text)

# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)