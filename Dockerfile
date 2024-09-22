# Use the official Python image from the Docker Hub
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory in the container
WORKDIR /app

# Install necessary dependencies for Playwright
RUN yum install -y libX11 libxcomposite libXcursor libXdamage libXi libXtst cups-libs libXScrnSaver alsa-lib pango at-spi2-atk gtk3
RUN pip install --upgrade pip

# Copy the requirements file to the container
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the source code into the container
COPY src/webscrape.py ${LAMBDA_TASK_ROOT}

# Set the handler
CMD ["webscrape.handler"]
