FROM python:3

MAINTAINER Christian Herzog <Pyroka3d@wherzog.de>

# For Alpine images:
# RUN apk add --no-cache tzdata

# set timezone
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 apt-get install cmake
RUN pip3 install --upgrade setuptools wheel

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "./collectDataVoltageV5.py"]