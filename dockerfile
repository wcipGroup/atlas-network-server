FROM python:3.8-alpine
RUN python3.8 -m pip install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
RUN pip3 install tensorflow
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
