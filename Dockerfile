# https://docs.docker.com/get-started/part2/#dockerfile
# Use an official Python runtime as a parent image
FROM python:2.7-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port available to the world outside this container
EXPOSE 80

# Define environment variable
ENV DB_URL localhost
# Example of a URL that could be hosted elsewhere, like CloudSQL
# ENV DB_URL 35.196.126.203
ENV DB_NAME businesses
ENV DB_USER postgres
ENV DB_PASSWD postgres 

# Run app.py when the container launches
CMD ["python", "app.py"]
