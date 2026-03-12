ARG NODE_BASE_IMAGE=docker.m.daocloud.io/node:20-alpine
ARG PYTHON_BASE_IMAGE=docker.m.daocloud.io/python:3.12-slim

FROM ${NODE_BASE_IMAGE} AS frontend-builder
ARG NPM_REGISTRY=https://registry.npmmirror.com

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry ${NPM_REGISTRY}
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM ${PYTHON_BASE_IMAGE} AS runtime
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV APP_SERVE_FRONTEND=true
ENV FRONTEND_DIST_DIR=/app/frontend/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
