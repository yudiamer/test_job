FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 BROWSER_HEADLESS=true
RUN apt-get update && apt-get install -y --no-install-recommends wget unzip ca-certificates fonts-liberation libnss3 libxi6 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libxss1 libxtst6 libasound2 libatk-bridge2.0-0 libgtk-3-0 libgbm-dev curl && rm -rf /var/lib/apt/lists/*
# Install Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb \
 && rm google-chrome-stable_current_amd64.deb
# Match chromedriver
RUN CHROME_MAJOR=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) \
 && DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}) \
 && wget -q https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip \
 && unzip chromedriver_linux64.zip -d /usr/local/bin \
 && rm chromedriver_linux64.zip \
 && chmod +x /usr/local/bin/chromedriver
WORKDIR /app
COPY config/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt
COPY . .
ENV CHROME_BIN=/usr/bin/google-chrome CHROMEDRIVER_PATH=/usr/local/bin/chromedriver DISPLAY=:99
ENTRYPOINT ["python", "run_automation.py"]
