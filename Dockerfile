# Build the React website.
FROM node:24-bookworm-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Run the Python API and serve the built website.
FROM python:3.13-slim
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/main.py backend/url_checks.py ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

CMD ["sh", "-c", "exec python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]