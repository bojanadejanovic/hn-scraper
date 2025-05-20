FROM python:3.11-slim

WORKDIR /app

COPY . .

# Optional: Copy env vars if using a .env file
# COPY .env .

RUN pip install -r requirements.txt

CMD ["python", "scraper.py"]
