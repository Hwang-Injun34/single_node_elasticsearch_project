FROM python:3.11-slim

# 필수 시스템 패키지 설치 (Playwright + PDF 처리 + MySQL/SSL용 최소)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    build-essential \
    default-libmysqlclient-dev \
    libssl-dev \
    curl \
    fonts-noto-cjk \
    libnss3 \
    libdbus-glib-1-2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir cryptography

# Playwright 설치
RUN pip install --upgrade playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright-browsers
RUN playwright install chromium

# 앱 복사 및 실행 권한 설정
COPY . .
RUN chmod +x /app/start.sh

CMD ["bash", "/app/start.sh"]
