FROM python:3.8-alpine
RUN python3.8 -m pip install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN python3.8 -m pip install -r requirements.txt
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
