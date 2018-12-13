FROM alpine

RUN apk update && apk add python3 py3-pip

RUN pip3 install redis websockets

ADD server.py /opt/server.py

ENTRYPOINT ["python3", "/opt/server.py"]
