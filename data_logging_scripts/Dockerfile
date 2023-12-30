FROM python:3

MAINTAINER Christian Herzog <Pyroka3d@wherzog.de>

# For Alpine images:
# RUN apk add --no-cache tzdata

# set timezone
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# from https://stackoverflow.com/questions/77144229/can-not-install-numpy 
RUN pip3 install --upgrade pip
# https://stackoverflow.com/questions/55506684/error-installing-cmake-in-a-docker-container-could-not-find-protobuf 
RUN apt-get update && apt-get -y install cmake protobuf-compiler
RUN pip3 install --upgrade setuptools wheel

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "./collectDataVoltageV5.py"]