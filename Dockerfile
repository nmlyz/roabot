FROM python:3.11
WORKDIR /bot

# 更新・日本語化
RUN apt-get update && \
apt-get -y install locales ffmpeg ca-certificates && \
apt-get -y upgrade && \
localedef -f UTF-8 -i ja_JP ja_JP.UTF-8

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm
ENV PYTHONHTTPSVERIFY=1

# pip install
COPY requirements.txt /bot/
RUN pip install -r requirements.txt

# すべてのファイルをコピー
COPY . /bot/

# cookies.txtの作成と設定
RUN echo "# Netscape HTTP Cookie File\n\
# https://curl.haxx.se/rfc/cookie_spec.html\n\
# This is a generated file! Do not edit.\n\
\n\
.youtube.com TRUE / TRUE 1735689600 CONSENT YES+cb\n\
.youtube.com TRUE / TRUE 1735689600 VISITOR_INFO1_LIVE 0123456789\n\
.youtube.com TRUE / TRUE 1735689600 YSC abcdefghijk\n\
.youtube.com TRUE / TRUE 1735689600 GPS 1" > /bot/app/cookies.txt

# 権限設定
RUN chmod 644 /bot/app/cookies.txt

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py