# Makefile for Brain AI Backend

.PHONY: help install dev test lint format clean migrate

help: ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	uv sync

dev: ## 启动开发服务器
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test: ## 运行测试
	uv run pytest

test-cov: ## 运行测试并生成覆盖率报告
	uv run pytest --cov=src --cov-report=html --cov-report=term

lint: ## 运行代码检查
	uv run flake8 src/
	uv run mypy src/

format: ## 格式化代码
	uv run black src/
	uv run isort src/

migrate: ## 运行数据库迁移
	uv run alembic upgrade head

migrate-create: ## 创建新迁移 (使用: make migrate-create MSG="描述")
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## 回滚一个迁移
	uv run alembic downgrade -1

shell: ## 启动 Python REPL
	uv run python

clean: ## 清理缓存文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

lock: ## 更新依赖锁文件
	uv lock

upgrade: ## 升级所有依赖
	uv sync --upgrade

add: ## 添加依赖 (使用: make add PKG=package-name)
	uv add $(PKG)

add-dev: ## 添加开发依赖 (使用: make add-dev PKG=package-name)
	uv add --dev $(PKG)

docker-build: ## 构建 Docker 镜像
	docker build -t brain-backend .

docker-run: ## 运行 Docker 容器
	docker run -p 8000:8000 --env-file .env brain-backend

.DEFAULT_GOAL := help
