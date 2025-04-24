FROM python:3.11-slim

WORKDIR /app

COPY hn_daily_report.py .

# Optional: Copy env vars if using a .env file
# COPY .env .

RUN pip install requests beautifulsoup4

CMD ["python", "hn_daily_report.py"]