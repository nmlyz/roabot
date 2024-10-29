from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "Server is Online."}

def run_flask():
    # Koyebの設定に合わせて8080ポートで起動
    app.run(host='0.0.0.0', port=8080)

def server_thread():
    t = Thread(target=run_flask)
    t.daemon = True  # メインプログラム終了時にスレッドも終了
    t.start()