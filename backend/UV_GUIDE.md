# UV 使用指南

## 什么是 uv？

[uv](https://github.com/astral-sh/uv) 是 Astral 推出的超快速 Python 包和项目管理器，用 Rust 编写。它比 pip 快 10-100 倍。

## 安装 uv

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip（不推荐）
```bash
pip install uv
```

## 常用命令

### 项目管理

```bash
# 初始化新项目（如果需要）
uv init

# 同步依赖（根据 pyproject.toml 和 uv.lock）
uv sync

# 仅安装生产依赖
uv sync --no-dev

# 添加依赖
uv add fastapi
uv add uvicorn[standard]

# 添加开发依赖
uv add --dev pytest
uv add --dev black

# 移除依赖
uv remove package-name

# 更新依赖
uv sync --upgrade

# 更新特定包
uv sync --upgrade-package fastapi

# 锁定依赖（生成 uv.lock）
uv lock
```

### 运行命令

```bash
# 在虚拟环境中运行命令
uv run python script.py
uv run pytest
uv run uvicorn src.main:app --reload

# 运行 alembic
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"

# 激活虚拟环境（如果需要）
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### Python 版本管理

```bash
# 安装特定 Python 版本
uv python install 3.11

# 使用特定 Python 版本
uv python pin 3.11

# 列出已安装的 Python 版本
uv python list
```

## 项目结构

使用 uv 后，项目会有以下文件：

```
backend/
├── pyproject.toml      # 项目配置和依赖
├── uv.lock             # 锁定的依赖版本（类似 poetry.lock）
├── .venv/              # 虚拟环境（自动创建）
├── .python-version     # Python 版本锁定（可选）
└── src/                # 源代码
```

## pyproject.toml 配置

本项目的 `pyproject.toml` 已配置好：

```toml
[project]
name = "brain-backend"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.115.0",
    "uvicorn[standard]==0.31.0",
    # ... 其他依赖
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "black==24.10.0",
    # ... 其他开发依赖
]
```

## 常见工作流

### 新机器上首次设置

```bash
# 1. 克隆仓库
git clone <repo-url>
cd brain/backend

# 2. 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 同步依赖
uv sync

# 4. 运行项目
uv run uvicorn src.main:app --reload
```

### 添加新依赖

```bash
# 1. 添加依赖（自动更新 pyproject.toml 和 uv.lock）
uv add httpx

# 2. 提交更改
git add pyproject.toml uv.lock
git commit -m "Add httpx dependency"
```

### 日常开发

```bash
# 启动开发服务器
uv run uvicorn src.main:app --reload

# 运行测试
uv run pytest

# 格式化代码
uv run black src/
uv run isort src/

# 类型检查
uv run mypy src/

# 数据库迁移
uv run alembic upgrade head
```

## 与 pip/venv 的对比

| 操作 | pip/venv | uv |
|------|----------|-----|
| 安装依赖 | `pip install -r requirements.txt` | `uv sync` |
| 添加依赖 | 手动编辑 requirements.txt + pip install | `uv add package` |
| 运行命令 | `python script.py` | `uv run python script.py` |
| 创建虚拟环境 | `python -m venv venv` | 自动创建 `.venv` |
| 速度 | 慢 | **快 10-100 倍** |
| 依赖锁定 | 需要额外工具 | 内置 `uv.lock` |

## 优势

✅ **超快速** - 比 pip 快 10-100 倍
✅ **依赖解析** - 智能解决依赖冲突
✅ **锁文件** - 自动生成 uv.lock，确保可重现的构建
✅ **统一工具** - 包管理 + 虚拟环境 + Python 版本管理
✅ **兼容性** - 完全兼容 pip，可读取 requirements.txt
✅ **现代化** - 遵循 PEP 标准，使用 pyproject.toml

## 故障排除

### 问题: uv.lock 文件冲突

```bash
# 重新生成 lock 文件
uv lock --upgrade
```

### 问题: 虚拟环境损坏

```bash
# 删除并重建虚拟环境
rm -rf .venv
uv sync
```

### 问题: Python 版本不匹配

```bash
# 安装正确的 Python 版本
uv python install 3.11
uv python pin 3.11
uv sync
```

### 问题: 依赖冲突

```bash
# 查看依赖树
uv tree

# 强制更新所有依赖
uv sync --upgrade --refresh
```

## 更多资源

- 官方文档: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- 迁移指南: https://docs.astral.sh/uv/guides/integration/

## 快速参考

```bash
# 项目初始化
uv init                  # 初始化新项目
uv sync                  # 安装依赖

# 依赖管理
uv add <pkg>            # 添加依赖
uv add --dev <pkg>      # 添加开发依赖
uv remove <pkg>         # 移除依赖
uv lock                 # 更新锁文件

# 运行命令
uv run <cmd>            # 在虚拟环境中运行
uv run python           # 启动 Python REPL
uv run pytest           # 运行测试

# Python 管理
uv python install 3.11  # 安装 Python 版本
uv python list          # 列出已安装版本
uv python pin 3.11      # 固定项目 Python 版本

# 信息查看
uv tree                 # 查看依赖树
uv pip list             # 列出已安装包
```
