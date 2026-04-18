# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install only the essential system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy your code into the container
COPY . .

# Install Python requirements
# Added --no-cache-dir to save space and prevent OOM errors
RUN pip install --no-cache-dir -r requirements.txt

# Tell Streamlit to run on port 8080
EXPOSE 8080

# Run the app and hide the Streamlit toolbar/header
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]