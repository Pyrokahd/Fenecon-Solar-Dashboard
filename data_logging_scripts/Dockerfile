FROM python:3

MAINTAINER Christian Herzog <Pyroka3d@wherzog.de>

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "./data_logging_scripts/collectDataVoltageV5.py"]