# Use an official Python runtime as a base image
FROM python:3

# Set the working directory to the /converter directory
WORKDIR /converter

# Copy the required contents into the container at /converter
ADD converter/service/converter.py          /converter
ADD scripts/gen_universe.py                 /converter
ADD repo/meta/schema                        /converter/repo/meta/schema
ADD scripts/requirements/requirements.txt   /converter/requirements.txt

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run converter.py when the container launches. -u to 'unbuffer' the output
CMD ["python3", "-u", "converter.py"]
