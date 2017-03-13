FROM nvidia/cuda:7.5-cudnn4-devel

MAINTAINER Nikki Aldeborgh <nikki.aldeborgh@digitalglobe.com>

RUN apt-get update -y && apt-get install -y \
    software-properties-common \
    python-software-properties \
    build-essential \
    python \
    python-dev \
    python-numpy \
    python-pip \
    python-scipy \
    ipython \
    libspatialite-dev \
    sqlite3 \
    libpq-dev \
    libcurl4-gnutls-dev \
    libproj-dev \
    libxml2-dev \
    libgeos-dev \
    libnetcdf-dev \
    libpoppler-dev \
    libspatialite-dev \
    libhdf4-alt-dev \
    libhdf5-serial-dev \
    vim \
    git \
    wget

RUN pip install gdal numpy ephem psycopg2 h5py theano geojson sklearn keras
RUN pip install git+https://github.com/DigitalGlobe/mltools

ADD ./bin /
COPY .theanorc /root/.theanorc
COPY keras.json /root/.keras/keras.json
