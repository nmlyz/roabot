FROM python:3.11
WORKDIR /bot

# システムの更新と必要なパッケージのインストール
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
ENV SSL_CERT_DIR=/etc/ssl/certs
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# pip installと証明書の設定
COPY requirements.txt /bot/
RUN pip install --upgrade pip && \
pip install --no-cache-dir -r requirements.txt && \
pip install certifi && \
python -m certifi

# すべてのファイルをコピー
COPY . /bot/

# 証明書の更新と権限設定
RUN update-ca-certificates --fresh && \
chmod -R 755 /etc/ssl/certs

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py