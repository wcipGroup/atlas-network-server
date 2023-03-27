FROM python:3.8-alpine
RUN apk update && apk add --no-cache \
    build-base \
    libressl-dev \
    libffi-dev \
    musl-dev \
    gcc \
    g++
RUN pip3 install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
