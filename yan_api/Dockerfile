FROM python:3.9.7

WORKDIR /code

COPY src/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY src/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]