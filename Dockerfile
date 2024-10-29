FROM python:3.11
WORKDIR /bot

# システムの更新と必要なパッケージのインストール
RUN apt-get update && \
apt-get -y install \
locales \
ffmpeg \
ca-certificates \
openssl \
curl \
&& apt-get -y upgrade \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# 日本語化
RUN localedef -f UTF-8 -i ja_JP ja_JP.UTF-8

# 環境変数の設定
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm
ENV PYTHONHTTPSVERIFY=0
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# 証明書の設定
RUN update-ca-certificates

# pip installと依存関係のインストール
COPY requirements.txt /bot/
RUN pip install --no-cache-dir --upgrade pip && \
pip install --no-cache-dir -r requirements.txt && \
pip install --no-cache-dir --upgrade yt-dlp && \
pip install --no-cache-dir certifi && \
python -m pip install --upgrade certifi

# pythonのSSL証明書を更新
RUN python -m certifi

# すべてのファイルをコピー
COPY . /bot/

# 証明書関連の権限設定
RUN chmod -R 644 /etc/ssl/certs/* && \
chmod 755 /etc/ssl/certs

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py