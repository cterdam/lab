FROM python:3.12-slim

WORKDIR /gpt

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
