FROM ubuntu:16.04
WORKDIR /root/1337
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip 

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY 1337.py .
COPY templates ./templates

ENV CACHE_DIR=/cache LANG=C.UTF-8
VOLUME /cache
EXPOSE 80

COPY uwsgi.ini .
CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
