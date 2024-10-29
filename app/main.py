import discord
import os
import yt_dlp
from collections import defaultdict
from server import server_thread
from datetime import datetime
import pytz
import asyncio
import certifi
import ssl

TOKEN = os.environ["TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

# SSL設定
ssl_context = ssl.create_default_context(cafile=certifi.where())

import discord
import os
import yt_dlp
from collections import defaultdict
from server import server_thread
from datetime import datetime
import pytz
import asyncio
import re
import urllib.parse
import json

TOKEN = os.environ["TOKEN"]
ADMIN_USER_ID = int(os.environ["ADMIN_USER_ID"])

# YT-DLP設定を更新
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
    }],
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['webpage', 'dash', 'hls'],
        },
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }
}

class MusicState:
    def __init__(self):
        self.voice_client = None
        self.current_url = None
        self.is_loop = False
        self.queue = []
        self.volume = 1.0
        self.now_playing = None

music_states = defaultdict(MusicState)

# DMの応答履歴を保持する辞書
dm_response_history = {}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

def extract_video_id(url):
    """URLからvideo_idを抽出"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?]*)',
        r'youtube\.com/shorts/([^&\n?]*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def play_music(voice_client, url, guild_id):
    state = music_states[guild_id]
    
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # androidクライアントとしてアクセス
                    ydl.params['extractor_args']['youtube']['player_client'] = ['android']
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: ydl.extract_info(url, download=False)
                    )
                    
                    if not info:
                        raise Exception("Failed to extract video info")
                    
                    url2 = info.get('url')
                    if not url2 and 'formats' in info:
                        # 最高品質の音声フォーマットを選択
                        formats = info['formats']
                        audio_formats = [f for f in formats if f.get('acodec') != 'none']
                        if audio_formats:
                            url2 = sorted(audio_formats, key=lambda x: x.get('abr', 0))[-1]['url']
                    
                    if not url2:
                        raise Exception("No audio URL found")

                    # FFmpegオプションを設定
                    ffmpeg_options = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn -b:a 128k'
                    }
                    
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_options)
                    break
                    
            except Exception as e:
                print(f"試行 {retry_count + 1} でエラー: {str(e)}")
                last_error = e
                retry_count += 1
                if retry_count >= max_retries:
                    raise last_error
                await asyncio.sleep(1)
        
        def after_playing(error):
            if error:
                print(f'再生エラー: {error}')
            elif state.is_loop and state.current_url:
                asyncio.run_coroutine_threadsafe(
                    play_music(voice_client, state.current_url, guild_id),
                    client.loop
                )
            elif state.queue:
                next_url = state.queue.pop(0)
                asyncio.run_coroutine_threadsafe(
                    play_music(voice_client, next_url, guild_id),
                    client.loop
                )
        
        if voice_client.is_playing():
            voice_client.stop()
        
        state.current_url = url
        state.now_playing = info.get('title', 'Unknown title')
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
    
    # 管理者への起動通知DM送信
    try:
        admin_user = await client.fetch_user(ADMIN_USER_ID)
        await admin_user.send(f'🚀 BOTが再起動されました！\n⏰ 起動時刻: {current_time}')
    except Exception as e:
        print(f"管理者への通知送信に失敗しました: {e}")
    
    # 各サーバーの適切なチャンネルへの起動通知送信
    for guild in client.guilds:
        notification_sent = False
        for channel in guild.text_channels:
            if channel.name in ['一般', 'general', 'bot', 'bot-log']:
                try:
                    await channel.send(f'🚀 BOTが再起動されました！\n⏰ 起動時刻: {current_time}')
                    notification_sent = True
                    break  # 送信成功したら次のサーバーへ
                except Exception as e:
                    continue  # 送信失敗時は次のチャンネルを試す
        
        if not notification_sent:
            print(f"サーバー '{guild.name}' への通知送信に失敗しました")
    
    await client.change_presence(activity=discord.Game(name="$help でコマンド一覧"))

@client.event
async def on_message(message):
    # BOTのメッセージは無視
    if message.author == client.user:
        return

    # DMの処理
    if message.guild is None:
        # 前回の応答から60秒以内は新しいメッセージを送信しない
        user_id = message.author.id
        current_time = datetime.now().timestamp()
        
        if user_id in dm_response_history:
            last_response_time = dm_response_history[user_id]
            if current_time - last_response_time < 60:  # 60秒のクールダウン
                return
        
        if message.content.startswith('$'):
            dm_response_history[user_id] = current_time
            await message.channel.send("❌ このボットはDMでは使用できません。サーバー内で使用してください。")
            return

    if message.content.startswith('$'):
        command = message.content.lower()
        
        # 通常のコマンド（helpなど）の処理
        if command == '$hello':
            await message.channel.send('Hello!')
            return
            
        elif command == '$help':
            help_text = """
**使用可能なコマンド一覧:**
`$hello` - BOTが挨拶を返します
`$help` - このヘルプメッセージを表示します
`$status` - BOTの動作状況を表示します
`$p [URL]` - YouTubeの音声を再生します
`$s` - 現在の曲をスキップします
`$l` - 現在の曲のループ再生を切り替えます
`$np` - 現在再生中の曲を表示します
`$q` - 現在のキューを表示します
`$vol [0-100]` - 音量を設定します
"""
            if message.author.id == ADMIN_USER_ID:
                help_text += "\n**管理者用コマンド:**\n`$shutdown` - BOTをシャットダウンします"
            
            await message.channel.send(help_text)
            return
            
        elif command == '$status':
            jst = pytz.timezone('Asia/Tokyo')
            current_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
            response_time = round(client.latency * 1000)
            
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
            return

        # 音楽関連のコマンド
        state = music_states[message.guild.id]
        
        if command.startswith('$p '):
            if not message.author.voice:
                await message.channel.send('❌ 先にボイスチャンネルに参加してください')
                return
                
            url = message.content[3:].strip()
            if not url.startswith('https://www.youtube.com/') and not url.startswith('https://youtu.be/'):
                await message.channel.send('❌ YouTubeのURLを指定してください')
                return
            
            try:
                loading_msg = await message.channel.send('🔄 音声を読み込み中です...')
                
                if not state.voice_client:
                    state.voice_client = await message.author.voice.channel.connect()
                elif state.voice_client.channel != message.author.voice.channel:
                    await state.voice_client.move_to(message.author.voice.channel)
                
                title = await play_music(state.voice_client, url, message.guild.id)
                await loading_msg.delete()
                
                if title:
                    await message.channel.send(f'🎵 再生開始: {title}')
                else:
                    await message.channel.send('❌ 再生できませんでした')
            except Exception as e:
                print(f'接続エラー: {e}')
                if 'loading_msg' in locals():
                    await loading_msg.delete()
                await message.channel.send('❌ 接続エラーが発生しました。しばらく待ってから再試行してください。')
        
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

        elif command == '$np':
            if state.now_playing:
                await message.channel.send(f'🎵 再生中: {state.now_playing}')
            else:
                await message.channel.send('❌ 現在再生中の曲はありません')

        elif command.startswith('$vol '):
            try:
                volume = int(message.content[5:])
                if not 0 <= volume <= 100:
                    await message.channel.send('❌ 音量は0から100の間で指定してください')
                    return
                
                state.volume = volume / 100
                if state.voice_client and state.voice_client.source:
                    state.voice_client.source.volume = state.volume
                await message.channel.send(f'🔊 音量を{volume}%に設定しました')
            except ValueError:
                await message.channel.send('❌ 正しい数値を指定してください')

        elif command == '$q':
            if not state.queue:
                await message.channel.send('📝 再生キューは空です')
                return
            
            queue_text = "**再生キュー:**\n"
            for i, url in enumerate(state.queue, 1):
                queue_text += f"{i}. {url}\n"
            await message.channel.send(queue_text)
        
        elif command == '$shutdown' and message.author.id == ADMIN_USER_ID:
            await message.channel.send('⚡ BOTをシャットダウンします...')
            await client.close()

# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)