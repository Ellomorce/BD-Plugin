FROM python:3.10

WORKDIR /

COPY . .

RUN pip install --upgrade pip

EXPOSE 5003

ENV TZ "Asia/Taipei"
ENTRYPOINT ["python", "devserver.py"]