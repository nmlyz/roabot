import discord
import os
import yt_dlp
from collections import defaultdict
from server import server_thread
from datetime import datetime
import pytz
import asyncio

TOKEN = os.environ["TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

# YT-DLPの設定
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
    }],
}

# 音楽プレイヤーの状態管理用
class MusicState:
    def __init__(self):
        self.voice_client = None
        self.current_url = None
        self.is_loop = False
        self.queue = []

# サーバーごとの状態を管理
music_states = defaultdict(MusicState)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

# YouTube URLから音声を再生する関数
async def play_music(voice_client, url, guild_id):
    state = music_states[guild_id]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2)
            
            def after_playing(error):
                if error:
                    print(f'再生エラー: {error}')
                elif state.is_loop and state.current_url:
                    # ループが有効な場合、同じ曲を再度再生
                    asyncio.run_coroutine_threadsafe(
                        play_music(voice_client, state.current_url, guild_id),
                        client.loop
                    )
                elif state.queue:
                    # キューに曲がある場合、次の曲を再生
                    next_url = state.queue.pop(0)
                    asyncio.run_coroutine_threadsafe(
                        play_music(voice_client, next_url, guild_id),
                        client.loop
                    )
            
            if voice_client.is_playing():
                voice_client.stop()
            
            state.current_url = url
            voice_client.play(source, after=after_playing)
            
            return info.get('title', 'Unknown title')
            
    except Exception as e:
        print(f'Error: {e}')
        return None

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
        state = music_states[message.guild.id]
        
        # 音楽関連のコマンド
        if command.startswith('$p '):
            # ユーザーがVCに接続しているか確認
            if not message.author.voice:
                await message.channel.send('❌ 先にボイスチャンネルに参加してください')
                return
                
            url = message.content[3:].strip()
            if not url.startswith('https://www.youtube.com/') and not url.startswith('https://youtu.be/'):
                await message.channel.send('❌ YouTubeのURLを指定してください')
                return
            
            # ボイスチャンネルに接続
            if not state.voice_client:
                state.voice_client = await message.author.voice.channel.connect()
            elif state.voice_client.channel != message.author.voice.channel:
                await state.voice_client.move_to(message.author.voice.channel)
            
            # 音楽を再生
            title = await play_music(state.voice_client, url, message.guild.id)
            if title:
                await message.channel.send(f'🎵 再生開始: {title}')
            else:
                await message.channel.send('❌ 再生できませんでした')
        
        elif command == '$s':
            if state.voice_client and state.voice_client.is_playing():
                state.voice_client.stop()
                await message.channel.send('⏭️ スキップしました')
            else:
                await message.channel.send('❌ 現在再生中の曲はありません')
        
        elif command == '$l':
            if not state.voice_client or not state.voice_client.is_playing():
                await message.channel.send('❌ 現在再生中の曲はありません')
                return
            
            state.is_loop = not state.is_loop
            await message.channel.send(f'🔄 ループ再生: {"オン" if state.is_loop else "オフ"}')
        
        # その他の既存のコマンド
        elif command == '$hello':
            await message.channel.send('Hello!')
        
        elif command == '$help':
            help_text = """
**使用可能なコマンド一覧:**
`$hello` - BOTが挨拶を返します
`$help` - このヘルプメッセージを表示します
`$status` - BOTの動作状況を表示します
`$p [URL]` - YouTubeの音声を再生します
`$s` - 現在の曲をスキップします
`$l` - 現在の曲のループ再生を切り替えます
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