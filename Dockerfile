FROM python:3.11
WORKDIR /bot

# 更新・日本語化
RUN apt-get update && \
apt-get -y install locales ffmpeg && \
apt-get -y upgrade && \
localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV TERM xterm

# pip install
COPY requirements.txt /bot/
RUN pip install -r requirements.txt

# すべてのファイルをコピー
COPY . /bot/

# cookies.txtが存在しない場合は作成
RUN touch /bot/app/cookies.txt

# ポート開放
EXPOSE 8080

# 実行
CMD python app/main.py