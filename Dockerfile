# Dockerfile
FROM public.ecr.aws/lambda/python:3.10

# Copy project files
COPY . /var/task/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the CMD to your handler (file.function)
CMD ["main.handler"]
