#!/bin/bash

# 加密货币量化交易系统部署脚本
# 作者: AI Assistant
# 日期: 2024-01-15

set -e

echo "🚀 开始部署加密货币量化交易系统..."

# 检查 Docker 和 Docker Compose 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  环境变量文件 .env 不存在，从 env.example 复制..."
    cp env.example .env
    echo "📝 请编辑 .env 文件，配置必要的 API 密钥和参数"
    echo "   特别是以下配置项："
    echo "   - GATE_API_KEY: Gate.io API 密钥"
    echo "   - GATE_API_SECRET: Gate.io API 密钥"
    echo "   - CRYPTOPANIC_API_KEY: CryptoPanic API 密钥"
    echo ""
    read -p "配置完成后按 Enter 继续..."
fi

# 创建必要的目录
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

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down --remove-orphans

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build --no-cache

# 启动基础服务
echo "🚀 启动基础服务 (Redis, PostgreSQL)..."
docker-compose up -d redis postgres

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 启动后端服务
echo "🚀 启动后端服务..."
docker-compose up -d backend

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
sleep 15

# 启动前端服务
echo "🚀 启动前端服务..."
docker-compose up -d frontend

# 启动 Nginx 代理
echo "🚀 启动 Nginx 代理..."
docker-compose up -d nginx

# 启动数据采集服务
echo "🚀 启动数据采集服务..."
docker-compose up -d data_collector

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 系统访问地址："
echo "   - 主界面: http://localhost"
echo "   - API 文档: http://localhost/api"
echo "   - 健康检查: http://localhost/api/health"
echo ""
echo "🔧 管理命令："
echo "   - 查看日志: docker-compose logs -f [service_name]"
echo "   - 重启服务: docker-compose restart [service_name]"
echo "   - 停止服务: docker-compose down"
echo "   - 启动实盘交易: docker-compose --profile trading up -d"
echo "   - 启动监控: docker-compose --profile monitoring up -d"
echo ""
echo "⚠️  注意事项："
echo "   1. 首次启动需要下载数据，可能需要较长时间"
echo "   2. 请确保已正确配置 API 密钥"
echo "   3. 实盘交易功能默认关闭，需要手动启用"
echo "   4. 建议先在测试环境验证系统功能"
echo ""

# 显示实时日志
read -p "是否查看实时日志？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 显示实时日志 (按 Ctrl+C 退出)..."
    docker-compose logs -f
fi
