FROM python:3.8.1-slim-buster

MAINTAINER Tige Phillips <tige@ignw.io>

# This container runs the web layer

RUN apt-get update ;\
    apt-get -y upgrade

# PYTHON and TOOLS
##################

# Install Python, Git, and Curl
# RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3 python3-dev python3-pip git
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install git gcc

# Install Python Packages
ADD gag/requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Install the Cisco ACI toolkit
RUN git clone https://github.com/datacenter/acitoolkit.git
RUN cd acitoolkit && python setup.py install

# App install
#############
ADD gag gag
COPY settings.yml gag/
ADD gunicorn_config.py gunicorn_config.py
ADD boot.sh ./
RUN chmod +x boot.sh
RUN touch /var/log/gag-web-log.log

# Port to access the application on
EXPOSE 5000
ENV FLASK_APP gag.py


# Production
############
CMD ["./boot.sh"]