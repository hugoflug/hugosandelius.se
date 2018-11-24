FROM ubuntu:xenial-20181113
WORKDIR /root/tagga
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3 \
    python3-pip 

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY tagga.py .
COPY static ./static
COPY templates ./templates
COPY *.wav ./

ENV LANG=C.UTF-8
EXPOSE 80

COPY tagga.ini .
CMD [ "uwsgi", "--ini", "tagga.ini" ]
