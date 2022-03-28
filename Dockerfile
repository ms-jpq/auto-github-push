FROM python:alpine

RUN apk add --no-cache -- git

COPY ./agp /agp
ENTRYPOINT [ "python3", "-m", "agp" ]
