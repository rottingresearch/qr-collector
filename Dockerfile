# Use the official Python image from the Docker Hub
FROM python:3.12.7-slim

# Copy requirements.txt to the container
COPY requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python-dev-is-python3
RUN pip install -r requirements.txt

# Copying files
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python3", "app.py"]