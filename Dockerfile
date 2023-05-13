FROM python:3

MAINTAINER Christian Herzog <Pyroka3d@wherzog.de>

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
# expose port to outside of container
EXPOSE 8050


# Start over gunicorn wsgi instead
CMD gunicorn --bind 0.0.0.0:8050 wsgi
