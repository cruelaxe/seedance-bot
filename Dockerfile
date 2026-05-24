FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir requests python-telegram-bot==20.7 httpx

COPY . .

CMD ["python", "bot.py"]
