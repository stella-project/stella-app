FROM elasticsearch:7.4.2

ENV discovery.type=single-node

USER root

COPY requirements.txt requirements.txt

RUN yum install -y https://repo.ius.io/ius-release-el7.rpm && yum -y update && yum install -y python36u python36u-libs python36u-devel python36u-pip && pip3 install -r requirements.txt

COPY ./script /script
COPY ./app.py /app.py

RUN sed -i -e '2inohup python3 /app.py &\' /usr/local/bin/docker-entrypoint.sh
