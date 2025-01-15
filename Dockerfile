FROM python:3.9-slim

WORKDIR /app
COPY main.py /app/

CMD python main.py
