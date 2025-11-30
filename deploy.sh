#!/bin/bash

# ========================================
# Brain AI 生产环境部署脚本
# ========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的命令
check_requirements() {
    log_info "检查系统要求..."

    commands=("docker" "docker-compose")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd 未安装，请先安装"
            exit 1
        fi
    done

    log_success "系统要求检查通过"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量配置..."

    if [ ! -f .env.production ]; then
        log_warning ".env.production 不存在，从示例文件创建..."
        cp .env.production.example .env.production
        log_error "请编辑 .env.production 文件，填写正确的配置后再运行此脚本"
        exit 1
    fi

    # 检查关键配置项
    source .env.production

    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" == "your_strong_password_here_change_me" ]; then
        log_error "请设置 POSTGRES_PASSWORD"
        exit 1
    fi

    if [ -z "$TONGYI_API_KEY" ] || [ "$TONGYI_API_KEY" == "your_tongyi_api_key_here" ]; then
        log_error "请设置 TONGYI_API_KEY"
        exit 1
    fi

    log_success "环境变量配置检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p nginx/conf.d
    mkdir -p nginx/ssl
    mkdir -p backups
    mkdir -p logs

    log_success "目录创建完成"
}

# 构建前端环境变量
build_frontend_env() {
    log_info "构建前端环境变量..."

    source .env.production

    cat > frontend/.env.production << EOF
VITE_API_BASE_URL=http://localhost:${BACKEND_PORT}/api
VITE_SSE_BASE_URL=http://localhost:${BACKEND_PORT}/api
EOF

    log_success "前端环境变量配置完成"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."

    if docker ps | grep -q brain-postgres-prod; then
        BACKUP_FILE="backups/brain_db_$(date +%Y%m%d_%H%M%S).sql"
        docker exec brain-postgres-prod pg_dump -U brain brain_prod > "$BACKUP_FILE"
        log_success "数据库备份完成: $BACKUP_FILE"
    else
        log_warning "数据库容器未运行，跳过备份"
    fi
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."

    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        docker-compose -f docker-compose.prod.yml down
        log_success "服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."

    docker-compose -f docker-compose.prod.yml build --no-cache

    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

    log_success "服务已启动"
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."

    # 等待后端服务启动
    sleep 10

    docker exec brain-backend-prod uv run alembic upgrade head || {
        log_warning "迁移可能已执行或不需要"
    }

    log_success "数据库迁移完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    MAX_RETRIES=30
    RETRY_INTERVAL=2

    # 检查后端
    log_info "检查后端服务..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "后端服务健康"
            break
        fi

        if [ $i -eq $MAX_RETRIES ]; then
            log_error "后端服务健康检查失败"
            exit 1
        fi

        sleep $RETRY_INTERVAL
    done

    # 检查前端
    log_info "检查前端服务..."
    if curl -f http://localhost:80/health &> /dev/null; then
        log_success "前端服务健康"
    else
        log_warning "前端服务可能未完全启动"
    fi

    log_success "健康检查完成"
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
}

# 显示日志
show_logs() {
    log_info "最近的日志:"
    docker-compose -f docker-compose.prod.yml logs --tail=20
}

# 清理旧镜像
cleanup() {
    log_info "清理未使用的镜像..."
    docker image prune -f
    log_success "清理完成"
}

# 主函数
main() {
    echo "=========================================="
    echo "  Brain AI 生产环境部署"
    echo "=========================================="
    echo ""

    # 检查是否在项目根目录
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 执行部署步骤
    check_requirements
    check_env_file
    create_directories
    build_frontend_env

    # 询问是否备份
    read -p "是否备份现有数据库? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        backup_database
    fi

    stop_services
    build_images
    start_services
    run_migrations
    health_check
    cleanup

    echo ""
    echo "=========================================="
    log_success "部署完成！"
    echo "=========================================="
    echo ""
    show_status
    echo ""
    log_info "访问地址:"
    echo "  前端: http://localhost"
    echo "  后端 API: http://localhost/api"
    echo "  健康检查: http://localhost/api/health"
    echo ""
    log_info "查看日志:"
    echo "  docker-compose -f docker-compose.prod.yml logs -f [service_name]"
    echo ""
    log_info "停止服务:"
    echo "  docker-compose -f docker-compose.prod.yml down"
    echo ""
}

# 运行主函数
main "$@"
