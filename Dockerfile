FROM python:3.11-slim AS base

# Install system dependencies
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy code and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command: run both the bot and the dashboard
# The bot will connect to Discord using the token from the environment
# The dashboard listens on port 8000
CMD ["bash", "-c", "python -m bot.src.main & uvicorn dashboard.app:app --host 0.0.0.0 --port 8000"]