
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir scrapyd scrapyd-client

COPY . .
COPY scrapyd.conf /etc/scrapyd/scrapyd.conf

EXPOSE 6800

CMD ["scrapyd", "--pidfile="]
