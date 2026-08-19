# Build from the REPO ROOT so the portal/ folder is in the context:
#   docker build -f backend/Dockerfile -t zz-portal .
#   docker run -d --env-file backend/.env -p 8000:8000 zz-portal
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app.py .
COPY portal ./static          # served at /portal (client) and /portal/admin (admin)
ENV STATIC_DIR=static
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
