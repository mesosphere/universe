# Use an official Python runtime as a base image
FROM python:3

# Set the working directory to the package directory
WORKDIR /package

# Copy the current directory contents into the container at /package
ADD . /package

# Run helloworld.py when the container launches. -u flag makes sure the output is not buffered
CMD ["python3", "-u", "helloworld.py"]
