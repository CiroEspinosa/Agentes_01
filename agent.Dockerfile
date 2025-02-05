# Use an official Python runtime as a parent image
FROM python:3.12.4-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY coreagents/ /app

# Set the PYTHONPATH to include /app to ensure all modules are found
ENV PYTHONPATH=/app

# Expose the production port
EXPOSE 9001

# Set the entry point to the main application script
ENTRYPOINT ["python", "starter/oai/starter_agent.py"]

# Default agent parameters (can be overridden at runtime)
CMD ["default_agent", "9001"]
