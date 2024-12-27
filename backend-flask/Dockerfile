FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get install python3.8 -y
RUN apt-get install python3-pip -y
RUN python3.8 -m pip install --upgrade pip
RUN apt-get install 'ffmpeg'\
    'libsm6'\
    'libxext6'  -y
RUN apt-get install python3.8-dev -y

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

WORKDIR /app-src
COPY . /app-src/

RUN python3.8 -m pip install -r requirements.txt

# RUN chmod +x run.sh
# EXPOSE 6868
# CMD ["bash", "./run.sh"]
