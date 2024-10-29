import discord
import os
from server import server_thread
from datetime import datetime
import pytz

TOKEN = os.environ["TOKEN"]
# ログを送信したいユーザーのID（あなたのDiscord ID）を環境変数から取得
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "YOUR_DISCORD_ID"))  # あなたのDiscord IDを設定

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

async def send_log(log_text):
    """管理者にDMでログを送信する関数"""
    try:
        # 日本時間で現在時刻を取得
        jst = pytz.timezone('Asia/Tokyo')
        current_time = datetime.now(jst).strftime('%Y年%m月%d日 %H時%M分%S秒')
        
        # 管理者ユーザーを取得
        admin_user = await client.fetch_user(ADMIN_USER_ID)
        if admin_user:
            await admin_user.send(f"```\n[{current_time}] {log_text}\n```")
    except Exception as e:
        print(f"ログ送信エラー: {e}")

@client.event
async def on_ready():
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    
    print('='*50)
    print(f'[{current_time}] BOTが起動しました！')
    print(f'BOT名: {client.user.name}')
    print(f'BOT ID: {client.user.id}')
    print(f'Discord.py バージョン: {discord.__version__}')
    print('='*50)
    
    # 起動ログをDMに送信
    await send_log("BOTが起動しました")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$'):
        command = message.content.lower()
        
        # コマンド実行ログ
        await send_log(f"コマンド実行: {command} (実行者: {message.author.name})")
        
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
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
            
            status_text = f"""
**BOTステータス**
🤖 BOT名: {client.user.name}
⚡ 接続状態: オンライン
⏰ 現在時刻: {current_time}
🏓 Ping応答速度: {round(client.latency * 1000)}ms
(~50 = GOOD)
"""
            await message.channel.send(status_text)

@client.event
async def on_error(event, *args, **kwargs):
    """エラーが発生した場合のログ"""
    await send_log(f"エラーが発生しました: {event}")

# Koyeb用 サーバー立ち上げ
server_thread()

# 起動前にログを送信
print("BOTを起動します...")
client.run(TOKEN)