# Use an official Python runtime as a parent image
FROM python:3.10


# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app


# Install the dependencies
RUN pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define the command to run the application using Gunicorn
#The first app is the name of your Python file without the .py extension (e.g., app.py).
#The second app is the Flask application instance created inside that file (e.g., app = Flask(__name__)).

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]

