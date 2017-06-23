# Use an official Python runtime as a base image
FROM python:2

# Set the working directory to /app
WORKDIR /package

# Copy the current directory contents into the container at /app
ADD . /package

# Run helloworld.py when the container launches
CMD ["python", "-u", "helloworld.py"]
