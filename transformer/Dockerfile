# Use an official Python runtime as a base image
FROM python:3

# Set the working directory to the /transformer directory
WORKDIR /transformer

# Copy the required contents into the container at /transformer
ADD ./service/transform.py      /transformer
ADD ./scripts/gen_universe.py   /transformer
ADD ./repo/meta/schema          /transformer/repo/meta/schema

# Run transform.py when the container launches. -u flag makes sure the output is not buffered
CMD ["python3", "-u", "transform.py"]
