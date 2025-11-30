# Backend Dockerfile - 使用 uv 进行包管理

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 复制项目文件
COPY pyproject.toml .
COPY uv.lock* .

# 使用 uv 安装依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令 - 使用 uv run
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
