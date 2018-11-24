FROM ubuntu:xenial-20181113
WORKDIR /root/hatify
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libatlas-base-dev \
    libboost-python-dev \
    libgtk-3-dev \
    libx11-dev \
    pkg-config \
    python3 \
    python3-pip 

COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt

COPY hatify.py .
COPY shape_predictor_68_face_landmarks.dat .

ENV FILES_DIR=/static LANG=C.UTF-8
VOLUME /static
EXPOSE 80

COPY uwsgi.ini .
CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
