FROM python:3.8-alpine

RUN pip3 install --upgrade pip

RUN mkdir /app
WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

WORKDIR /app/src

RUN ["chmod", "+x", "wrapper.sh"]

CMD ["sh", "./wrapper.sh"]
