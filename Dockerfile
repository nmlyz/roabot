FROM python:3.11
WORKDIR /bot

# システムの更新とSSL証明書のインストール
RUN apt-get update && \
apt-get -y install locales ffmpeg ca-certificates openssl && \
apt-get -y upgrade && \
update-ca-certificates && \
localedef -f UTF-8 -i ja_JP ja_JP.UTF-8

# 環境変数の設定
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm
ENV PYTHONHTTPSVERIFY=1

# SSL証明書の設定
RUN mkdir -p /etc/ssl/certs && \
update-ca-certificates

# pip installと依存関係のインストール
COPY requirements.txt /bot/
RUN pip install --no-cache-dir -r requirements.txt && \
pip install --no-cache-dir certifi urllib3

# すべてのファイルをコピー
COPY . /bot/

# cookies.txtの作成と権限設定
RUN touch /bot/app/cookies.txt && \
chmod 644 /bot/app/cookies.txt

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py