# syntax=docker/dockerfile:1
# Our project is a Python application, so we'll use the official Python image
# as a parent image. This image already contains all of the tools we need to
# install Python dependencies.
FROM python:3.8-slim-buster
# Set the working directory to /app
WORKDIR /app
# Copy needed files to the container at /app
COPY ./tenda_controller.py /app
COPY ./tenda_scraper.py /app
COPY ./tenda_controller.html /app
COPY ./requirements.txt /app
# Create "/config" directory for config file
RUN mkdir /config
# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# Run tenda_controller.py when the container launches
CMD ["python", "tenda_controller.py"]
# Environment variables
ENV ROUTER_IP "192.168.1.1"
# Make port 80 available to the world outside this container
EXPOSE 80