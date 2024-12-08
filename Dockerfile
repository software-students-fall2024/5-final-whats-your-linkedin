# Base Image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /webapp

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

RUN pip install flask
RUN pip install psycopg2-binary
RUN pip install pymongo
RUN pip install bcrypt 
RUN pip install python-dotenv

# Ensure pipenv is in PATH
ENV PATH="/root/.local/bin:$PATH"

RUN pipenv lock

# Install dependencies using the new Pipfile.lock
RUN pipenv install --system --deploy

# Copy the rest of the application code
COPY webapp/ /webapp

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]