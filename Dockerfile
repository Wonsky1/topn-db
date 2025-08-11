FROM python:3.11-slim-buster

WORKDIR /app
# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh

# Expose port
EXPOSE 8000

ARG DATABASE_URL

# Записуємо у змінні середовища
ENV DATABASE_URL=${DATABASE_URL}

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
