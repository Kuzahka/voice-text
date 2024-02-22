FROM python:3.10-slim
RUN mkdir /app
WORKDIR /app
COPY . /app
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt --no-cache-dir
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]