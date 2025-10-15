#!/bin/bash

echo "🧪 测试加密货币量化交易系统部署..."
echo ""

# 测试后端健康检查
echo "1. 测试后端健康检查..."
if curl -f -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ 后端健康检查通过"
else
    echo "❌ 后端健康检查失败"
fi

# 测试前端页面
echo "2. 测试前端页面..."
if curl -f -s http://localhost:8080/ > /dev/null; then
    echo "✅ 前端页面可访问"
else
    echo "❌ 前端页面不可访问"
fi

# 测试数据API
echo "3. 测试数据API..."
response=$(curl -s http://localhost:8080/api/data/status)
if echo "$response" | grep -q "success"; then
    echo "✅ 数据API正常"
else
    echo "❌ 数据API异常"
fi

# 测试模型API
echo "4. 测试模型API..."
response=$(curl -s http://localhost:8080/api/model/list)
if echo "$response" | grep -q "success"; then
    echo "✅ 模型API正常"
else
    echo "❌ 模型API异常"
fi

# 检查服务状态
echo "5. 检查Docker服务状态..."
docker-compose ps

echo ""
echo "📊 系统访问信息："
echo "   - 主界面: http://localhost:8080"
echo "   - API 健康检查: http://localhost:8080/api/health"
echo "   - 数据状态: http://localhost:8080/api/data/status"
echo "   - 模型列表: http://localhost:8080/api/model/list"
echo ""
echo "🔧 管理命令："
echo "   - 查看日志: docker-compose logs -f [service_name]"
echo "   - 重启服务: docker-compose restart [service_name]"
echo "   - 停止服务: docker-compose down"
echo "   - 启动实盘交易: docker-compose --profile trading up -d"
echo "   - 启动监控: docker-compose --profile monitoring up -d"
echo ""
echo "✅ 部署测试完成！"
