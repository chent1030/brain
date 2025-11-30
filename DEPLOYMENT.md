# Brain AI 生产环境部署指南

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [配置说明](#配置说明)
- [运维管理](#运维管理)
- [故障排查](#故障排查)
- [安全建议](#安全建议)

## 🖥️ 系统要求

### 硬件要求

- **CPU**: 2核心以上
- **内存**: 4GB 以上（推荐 8GB）
- **存储**: 20GB 以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+) 或 macOS
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Git**: 2.0+

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd brain
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.production.example .env.production

# 编辑环境变量
vim .env.production
```

**必须修改的配置**:
- `POSTGRES_PASSWORD`: 数据库密码（务必使用强密码）
- `TONGYI_API_KEY`: 通义千问 API Key
- `CORS_ORIGINS`: 允许的前端域名

### 3. 执行部署

```bash
# 给部署脚本执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

部署脚本会自动完成：
- ✅ 检查系统要求
- ✅ 验证配置文件
- ✅ 构建 Docker 镜像
- ✅ 启动所有服务
- ✅ 运行数据库迁移
- ✅ 执行健康检查

### 4. 访问应用

部署成功后，访问：

- **前端**: http://your-server-ip
- **后端 API**: http://your-server-ip/api
- **健康检查**: http://your-server-ip/api/health

## 📝 详细步骤

### 步骤 1: 准备服务器

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用 docker 组权限
exit
```

#### CentOS/RHEL

```bash
# 更新系统
sudo yum update -y

# 安装 Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录
exit
```

### 步骤 2: 配置防火墙

```bash
# Ubuntu/Debian (使用 ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (使用 firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 步骤 3: 配置 SSL (可选但推荐)

#### 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot  # Ubuntu/Debian
# 或
sudo yum install certbot  # CentOS/RHEL

# 生成证书
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem
```

然后在 `nginx/conf.d/brain.conf` 中启用 HTTPS 配置（取消注释）。

### 步骤 4: 配置域名

在你的 DNS 服务商配置 A 记录：

```
A    @              your-server-ip
A    www            your-server-ip
```

### 步骤 5: 更新 Nginx 配置

编辑 `nginx/conf.d/brain.conf`，将 `server_name _;` 替换为你的域名：

```nginx
server_name yourdomain.com www.yourdomain.com;
```

## ⚙️ 配置说明

### 环境变量详解

#### 数据库配置

```bash
POSTGRES_USER=brain                    # 数据库用户名
POSTGRES_PASSWORD=strong_password_123  # 数据库密码（务必修改）
POSTGRES_DB=brain_prod                 # 数据库名
POSTGRES_PORT=5432                     # 数据库端口
```

#### API Keys

```bash
TONGYI_API_KEY=sk-xxxxx  # 通义千问 API Key（从阿里云获取）
```

#### 应用配置

```bash
ENVIRONMENT=production   # 环境：production/staging/development
DEBUG=false             # 调试模式（生产环境必须为 false）
```

#### 服务端口

```bash
BACKEND_PORT=8000       # 后端服务端口
FRONTEND_PORT=3000      # 前端服务端口
NGINX_HTTP_PORT=80      # Nginx HTTP 端口
NGINX_HTTPS_PORT=443    # Nginx HTTPS 端口
```

#### CORS 配置

```bash
# 允许的前端域名（多个用逗号分隔）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🔧 运维管理

### 查看服务状态

```bash
docker-compose -f docker-compose.prod.yml ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
```

### 停止服务

```bash
docker-compose -f docker-compose.prod.yml down
```

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新部署
./deploy.sh
```

### 数据库备份

#### 手动备份

```bash
# 创建备份
docker exec brain-postgres-prod pg_dump -U brain brain_prod > backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 自动备份（使用 cron）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * cd /path/to/brain && docker exec brain-postgres-prod pg_dump -U brain brain_prod > backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

#### 恢复备份

```bash
# 停止后端服务
docker-compose -f docker-compose.prod.yml stop backend

# 恢复数据库
cat backups/backup_20240101_020000.sql | docker exec -i brain-postgres-prod psql -U brain brain_prod

# 启动后端服务
docker-compose -f docker-compose.prod.yml start backend
```

### 监控

#### 查看资源使用

```bash
docker stats
```

#### 健康检查

```bash
# 后端健康检查
curl http://localhost/api/health

# 前端健康检查
curl http://localhost/health
```

## 🐛 故障排查

### 问题：服务无法启动

**检查日志**:
```bash
docker-compose -f docker-compose.prod.yml logs
```

**常见原因**:
1. 端口被占用
2. 环境变量配置错误
3. 磁盘空间不足

### 问题：数据库连接失败

**检查数据库是否运行**:
```bash
docker-compose -f docker-compose.prod.yml ps postgres
```

**查看数据库日志**:
```bash
docker-compose -f docker-compose.prod.yml logs postgres
```

**验证数据库连接**:
```bash
docker exec -it brain-postgres-prod psql -U brain -d brain_prod
```

### 问题：前端无法连接后端

**检查环境变量**:
- 确认 `frontend/.env.production` 中的 API 地址正确
- 确认 CORS 配置包含前端域名

**检查网络**:
```bash
docker network inspect brain_brain-network
```

### 问题：MCP 工具调用失败

**检查 npm 和 npx 安装**:
```bash
docker exec brain-backend-prod which npx
docker exec brain-backend-prod npx --version
```

**查看 MCP 配置**:
```bash
docker exec brain-backend-prod cat /app/src/config/mcp_config.json
```

## 🔒 安全建议

### 1. 使用强密码

- 数据库密码至少 16 位，包含大小写字母、数字和特殊字符
- 定期更换密码

### 2. 启用 HTTPS

- 使用 Let's Encrypt 免费 SSL 证书
- 强制 HTTP 跳转到 HTTPS

### 3. 限制数据库访问

编辑 `docker-compose.prod.yml`，移除数据库的端口映射：

```yaml
postgres:
  # 注释掉这行，只允许容器内部访问
  # ports:
  #   - "5432:5432"
```

### 4. 配置防火墙

只开放必要的端口（80, 443）。

### 5. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker-compose -f docker-compose.prod.yml pull
./deploy.sh
```

### 6. 监控日志

定期检查日志文件，查找异常访问或错误。

### 7. 数据备份

- 每天自动备份数据库
- 定期测试备份恢复流程

## 📞 技术支持

如遇问题，请：

1. 查看日志文件
2. 检查本文档的故障排查章节
3. 在项目 GitHub Issues 提交问题

## 📄 许可证

请参考项目根目录的 LICENSE 文件。
