FROM python:3.8

WORKDIR /app
COPY main.py /app/

CMD python main.py