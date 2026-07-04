FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN  pip install -r requirements.txt -t /var/task

COPY . .

CMD ["main.handler"]
