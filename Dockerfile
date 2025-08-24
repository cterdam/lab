FROM python:3.12-slim

WORKDIR /gpt

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -U -r requirements.txt

COPY . .
