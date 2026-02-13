FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestor/ ingestor/

EXPOSE 8088

CMD ["python", "-m", "ingestor.main"]
