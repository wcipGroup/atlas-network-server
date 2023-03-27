FROM python:3.9-alpine
RUN python3.9 -m pip install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
RUN python3.9 -m pip install --upgrade https://storage.googleapis.com/tensorflow/windows/cpu/tensorflow_cpu-2.10.0-cp310-cp310-win_amd64.whl
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
