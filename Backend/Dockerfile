# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy the Flask API code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Start the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
