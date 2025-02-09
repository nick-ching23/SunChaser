FROM python:3.11-slim

WORKDIR /app

COPY batch_inference.py /app/

RUN pip install --no-cache-dir requests

CMD ["python", "batch_inference.py"]