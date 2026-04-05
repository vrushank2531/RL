FROM python:3.11-slim

WORKDIR /app

COPY code_debugger_env/server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything the server needs (models.py lives inside server/)
COPY code_debugger_env/server/ .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
