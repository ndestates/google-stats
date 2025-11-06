# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for python command (optional)
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Set Python environment variables
ENV PYTHONPATH=/var/www/html
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1