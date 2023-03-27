FROM python:3.9-alpine
RUN python3.9 -m pip install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
