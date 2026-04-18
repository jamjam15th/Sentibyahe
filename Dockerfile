# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (needed for some ML libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy your code into the container
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Tell Streamlit to run on port 8080 (App Platform default)
EXPOSE 8080

# Run the app without the Streamlit header/menu
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--client.toolbarMode=hidden"]