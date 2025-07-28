FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY output ./output

EXPOSE 5000
CMD ["python", "app/main.py"]