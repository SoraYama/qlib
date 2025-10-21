#!/bin/bash

# 加密货币量化交易系统部署脚本
# 作者: AI Assistant
# 日期: 2024-01-15
# 用法: ./deploy.sh [start|stop|restart|status|logs|build]

set -e

# 显示使用说明
show_usage() {
    echo "🚀 加密货币量化交易系统管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     - 启动所有服务"
    echo "  stop      - 停止所有服务"
    echo "  restart   - 重启所有服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看实时日志"
    echo "  build     - 重新构建并启动服务"
    echo "  clean     - 清理所有容器和镜像"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 stop     # 停止服务"
    echo "  $0 restart  # 重启服务"
    echo "  $0 status   # 查看状态"
    echo "  $0 logs     # 查看日志"
}

# 检查 Docker 和 Docker Compose 是否安装
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f .env ]; then
        echo "⚠️  环境变量文件 .env 不存在，从 env.example 复制..."
        if [ -f env.example ]; then
            cp env.example .env
            echo "📝 请编辑 .env 文件，配置必要的 API 密钥和参数"
            echo "   特别是以下配置项："
            echo "   - GATE_API_KEY: Gate.io API 密钥"
            echo "   - GATE_API_SECRET: Gate.io API 密钥"
            echo "   - CRYPTOPANIC_API_KEY: CryptoPanic API 密钥"
            echo ""
            read -p "配置完成后按 Enter 继续..."
        else
            echo "❌ env.example 文件不存在，请手动创建 .env 文件"
            exit 1
        fi
    fi
}

# 创建必要的目录
create_directories() {
    echo "📁 创建必要的目录..."
    mkdir -p logs
    mkdir -p data/gate/source
    mkdir -p data/gate/normalize
    mkdir -p data/news/source
    mkdir -p data/news/normalize
    mkdir -p data/onchain/source
    mkdir -p data/onchain/normalize
    mkdir -p reports
    mkdir -p ssl

    # 设置目录权限
    chmod 755 logs
    chmod 755 data
    chmod 755 reports
}

# 启动服务
start_services() {
    echo "🚀 开始启动加密货币量化交易系统..."

    check_dependencies
    check_env_file
    create_directories

    # 停止现有服务
    echo "🛑 停止现有服务..."
    docker compose down --remove-orphans

    # 构建镜像
    echo "🔨 构建 Docker 镜像..."
    # 检查基础镜像是否存在
    echo "🔍 检查基础镜像..."
    if ! docker images | grep -q "python.*3.9-slim"; then
        echo "📥 拉取 python:3.9-slim..."
        docker pull python:3.9-slim
    fi
    if ! docker images | grep -q "node.*18-alpine"; then
        echo "📥 拉取 node:18-alpine..."
        docker pull node:18-alpine
    fi
    # 构建自定义镜像
    docker compose build

    # 启动基础服务
    echo "🚀 启动基础服务 (Redis, PostgreSQL)..."
    docker compose up -d redis postgres

    # 等待数据库启动
    echo "⏳ 等待数据库启动..."
    sleep 10

    # 启动后端服务
    echo "🚀 启动后端服务..."
    docker compose up -d backend

    # 等待后端服务启动
    echo "⏳ 等待后端服务启动..."
    sleep 15

    # 启动前端服务
    echo "🚀 启动前端服务..."
    docker compose up -d frontend

    # 启动 Nginx 代理
    echo "🚀 启动 Nginx 代理..."
    docker compose up -d nginx

    # 启动数据采集服务
    echo "🚀 启动数据采集服务..."
    docker compose up -d data_collector

    # 检查服务状态
    echo "🔍 检查服务状态..."
    docker compose ps

    # 显示访问信息
    show_access_info
}

# 停止服务
stop_services() {
    echo "🛑 停止加密货币量化交易系统..."
    docker compose down --remove-orphans
    echo "✅ 所有服务已停止"
}

# 重启服务
restart_services() {
    echo "🔄 重启加密货币量化交易系统..."
    stop_services
    sleep 5
    start_services
}

# 查看服务状态
show_status() {
    echo "🔍 服务状态："
    docker compose ps
    echo ""
    echo "📊 系统资源使用情况："
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 查看日志
show_logs() {
    echo "📋 显示实时日志 (按 Ctrl+C 退出)..."
    docker compose logs -f
}

# 重新构建服务
rebuild_services() {
    echo "🔨 重新构建并启动服务..."
    check_dependencies
    check_env_file
    create_directories

    # 停止现有服务
    echo "🛑 停止现有服务..."
    docker compose down --remove-orphans

    # 清理镜像
    echo "🧹 清理旧镜像..."
    # 检查基础镜像是否存在
    echo "🔍 检查基础镜像..."
    if ! docker images | grep -q "python.*3.9-slim"; then
        echo "📥 拉取 python:3.9-slim..."
        docker pull python:3.9-slim
    fi
    if ! docker images | grep -q "node.*18-alpine"; then
        echo "📥 拉取 node:18-alpine..."
        docker pull node:18-alpine
    fi
    # 然后构建自定义镜像
    docker compose build --no-cache

    # 启动所有服务
    echo "🚀 启动所有服务..."
    docker compose up -d

    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 20

    # 检查服务状态
    echo "🔍 检查服务状态..."
    docker compose ps

    show_access_info
}

# 清理所有容器和镜像
clean_all() {
    echo "🧹 清理所有容器和镜像..."
    read -p "⚠️  这将删除所有容器、镜像和卷，确定继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose down --remove-orphans --volumes --rmi all
        docker system prune -af
        echo "✅ 清理完成"
    else
        echo "❌ 取消清理操作"
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "✅ 部署完成！"
    echo ""
    echo "📊 系统访问地址："
    echo "   - 主界面: http://localhost"
    echo "   - API 文档: http://localhost/api"
    echo "   - 健康检查: http://localhost/api/health"
    echo ""
    echo "🔧 管理命令："
    echo "   - 查看日志: $0 logs"
    echo "   - 重启服务: $0 restart"
    echo "   - 停止服务: $0 stop"
    echo "   - 查看状态: $0 status"
    echo "   - 启动实盘交易: docker compose --profile trading up -d"
    echo "   - 启动监控: docker compose --profile monitoring up -d"
    echo ""
    echo "⚠️  注意事项："
    echo "   1. 首次启动需要下载数据，可能需要较长时间"
    echo "   2. 请确保已正确配置 API 密钥"
    echo "   3. 实盘交易功能默认关闭，需要手动启用"
    echo "   4. 建议先在测试环境验证系统功能"
    echo ""
}

# 主程序逻辑
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build)
        rebuild_services
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
