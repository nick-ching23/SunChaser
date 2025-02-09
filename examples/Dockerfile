FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
COPY batch_inference.py /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data /app/output

ENTRYPOINT ["python", "batch_inference.py"]