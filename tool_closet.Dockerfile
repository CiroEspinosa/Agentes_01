# Use an official Python runtime as a parent image
FROM python:3.12.4-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY tools/closet_api /app
COPY coreagents/factory/web_factory.py /app/factory/web_factory.py
COPY coreagents/utils/logging_config.py /app/utils/logging_config.py

# Set the PYTHONPATH to include /app to ensure all modules are found
ENV PYTHONPATH=/app

# Expose the production port
EXPOSE 7120

ENTRYPOINT ["python", "main.py"]
