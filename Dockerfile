FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source and scripts
COPY src ./src
COPY scripts ./scripts
COPY .env ./

# Set Python path to src (so imports like "from incident_iq..." work)
ENV PYTHONPATH=/app/src

# Default command
CMD ["python", "scripts/run_test.py"]
