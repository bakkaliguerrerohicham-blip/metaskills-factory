FROM python:3.11-slim

WORKDIR /app

RUN apk add --no-cache curl 2>/dev/null || (apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*)

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8091

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8091"]
