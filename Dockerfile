FROM python:3.9-slim

WORKDIR /

COPY app.py .
COPY requirements.txt .
COPY . .
COPY ./assets/prize1.mp3 ./assets/
COPY ./assets/prize2.mp3 ./assets/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "./app.py"]
