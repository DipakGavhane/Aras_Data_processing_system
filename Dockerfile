# Use the full Python 3.10 image instead of slim to avoid missing dependencies
FROM python:3.10

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    curl

# Install Chromium (from distro repository; version may vary but should be compatible with Chrome for Testing 135.0.7049.42)
RUN apt-get update && apt-get install -y --no-install-recommends chromium

# Set environment variable for the ChromeDriver version we want
ENV CHROMEDRIVER_VERSION=135.0.7049.42

# Download and install ChromeDriver for Linux64 from Chrome for Testing
RUN wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /usr/local/bin/chromedriver-linux64


# Install missing dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libgbm-dev \
    libgtk-3-dev \
    libx11-xcb1 \
    libxcomposite-dev \
    libxcursor-dev \
    libxdamage-dev \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 5000

# Define the command to run your application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
