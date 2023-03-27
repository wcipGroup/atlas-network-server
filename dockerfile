FROM python:3.8-alpine
RUN apk add --no-cache --virtual .build-deps \
        build-base \
        bash \
        git \
        curl \
        wget \
        ca-certificates \
        libstdc++ \
        g++ \
        libx11 \
        libxrender \
        libxext \
        libssl1.1 \
        libcrypto1.1 \
        libjpeg-turbo \
        libpng \
        freetype \
        libgcc \
        libffi-dev \
        openssl-dev \
        python3-dev \
        libxml2 \
        libxml2-dev \
        libxslt-dev \
        lapack-dev \
        gfortran \
        openblas-dev \
        python3-tkinter \
        zlib-dev \
        jpeg-dev \
        freetype-dev \
        lcms2-dev \
        openjpeg-dev \
        tiff-dev \
        tk-dev \
        tcl-dev \
        harfbuzz-dev \
        fribidi-dev \
        libpng-dev \
        libjpeg-turbo-dev \
        freetype-dev \
        libwebp-dev \
        gcc \
        musl-dev \
        linux-headers \
        make \
    && rm -rf /var/cache/apk/*
RUN pip3 install --upgrade pip
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt
WORKDIR /app/src
RUN ["chmod", "+x", "wrapper.sh"]
CMD ["sh", "./wrapper.sh"]
