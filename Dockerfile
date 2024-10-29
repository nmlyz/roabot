FROM python:3.11
WORKDIR /bot

# システムの更新とブラウザ関連パッケージのインストール
RUN apt-get update && \
apt-get -y install locales ffmpeg ca-certificates chromium chromium-driver && \
apt-get -y upgrade && \
localedef -f UTF-8 -i ja_JP ja_JP.UTF-8 && \
update-ca-certificates

# 環境変数の設定
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm
ENV PYTHONHTTPSVERIFY=1
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium

# pip installと依存関係のインストール
COPY requirements.txt /bot/
RUN pip install --no-cache-dir -r requirements.txt && \
pip install --no-cache-dir --upgrade yt-dlp browser-cookie3 selenium

# すべてのファイルをコピー
COPY . /bot/

# 必要なディレクトリの作成
RUN mkdir -p /bot/app/temp && \
chmod 777 /bot/app/temp

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py