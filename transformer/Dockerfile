# Use an official Python runtime as a base image
FROM python:3

# Set the working directory to the /transformer directory
WORKDIR /transformer

# Copy the required contents into the container at /transformer
ADD transformer/service/transform.py        /transformer
ADD scripts/gen_universe.py                 /transformer
ADD repo/meta/schema                        /transformer/repo/meta/schema
ADD scripts/requirements/requirements.txt   /transformer/requirements.txt

# Install the required depen
RUN pip install --no-cache-dir -r requirements.txt

# Run transform.py when the container launches. -u to 'unbuffer' the output
CMD ["python3", "-u", "transform.py"]
