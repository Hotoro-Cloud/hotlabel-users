FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/ensure_db_ready.py
RUN chmod +x start.py

CMD ["python", "start.py"]
