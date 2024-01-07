FROM python:3.12
WORKDIR /Test
COPY /app .
COPY requirements.txt .
RUN pip install --no-cache-dir -r /Test/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
