# Use an official Python runtime as a base image
FROM python:2

# Set the working directory to /app
WORKDIR /package

# Copy the current directory contents into the container at /app
ADD . /package

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run helloworld.py when the container launches
CMD ["python", "-u", "helloworld.py"]
