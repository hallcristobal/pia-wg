FROM python:3.11-alpine AS builder

WORKDIR /app

RUN apk update && apk add wireguard-tools
RUN python3 -m pip config set global.break-system-packages true

FROM builder AS runner

COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "/app/generate-config.py"]

