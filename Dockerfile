FROM python:alpine

RUN apk add --no-cache -- git

COPY ./agp /agp/
COPY ./main.py /
WORKDIR /
ENTRYPOINT [ "/main.py" ]
