# 部署指南

## 系统要求

### 硬件要求
- **CPU**: 4 核心以上
- **内存**: 8GB 以上
- **存储**: 100GB 以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.9+
- **Node.js**: 18+

## 部署方式

### 方式一：Docker Compose 部署（推荐）

#### 1. 环境准备

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp web-ui/env.example web-ui/.env

# 编辑配置文件
nano web-ui/.env
```

配置必要的 API 密钥：

```bash
# Gate.io API 配置
GATE_API_KEY=your_gate_api_key
GATE_API_SECRET=your_gate_api_secret

# 新闻 API 配置
CRYPTOPANIC_API_KEY=your_cryptopanic_api_key

# 链上数据 API 配置
GLASSNODE_API_KEY=your_glassnode_api_key

# 其他配置
TRADING_ENABLED=false
SANDBOX_MODE=true
```

#### 3. 一键部署

```bash
# 进入项目目录
cd /path/to/qlib

# 运行部署脚本
chmod +x web-ui/deploy.sh
./web-ui/deploy.sh
```

#### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 测试 API
curl http://localhost:5000/health
```

### 方式二：手动部署

#### 1. 后端部署

```bash
# 安装 Python 依赖
cd web-ui/backend
pip install -r requirements.txt

# 启动后端服务
python app.py
```

#### 2. 前端部署

```bash
# 安装 Node.js 依赖
cd web-ui/frontend
npm install

# 构建生产版本
npm run build

# 启动前端服务
npm start
```

#### 3. Nginx 配置

```bash
# 安装 Nginx
sudo apt update
sudo apt install nginx

# 复制配置文件
sudo cp web-ui/nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp web-ui/nginx/conf.d/default.conf /etc/nginx/sites-available/crypto-trading

# 启用站点
sudo ln -s /etc/nginx/sites-available/crypto-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 服务配置

### 数据库配置

#### PostgreSQL 配置

```bash
# 创建数据库
sudo -u postgres createdb crypto_trading

# 创建用户
sudo -u postgres createuser trading_user

# 设置密码
sudo -u postgres psql -c "ALTER USER trading_user PASSWORD 'trading_password';"

# 授权
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE crypto_trading TO trading_user;"
```

#### Redis 配置

```bash
# 安装 Redis
sudo apt install redis-server

# 配置 Redis
sudo nano /etc/redis/redis.conf

# 启动服务
sudo systemctl start redis
sudo systemctl enable redis
```

### 监控配置

#### Prometheus 配置

```bash
# 创建 Prometheus 用户
sudo useradd --no-create-home --shell /bin/false prometheus

# 创建配置目录
sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus

# 复制配置文件
sudo cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml

# 设置权限
sudo chown -R prometheus:prometheus /etc/prometheus
sudo chown -R prometheus:prometheus /var/lib/prometheus
```

#### Grafana 配置

```bash
# 安装 Grafana
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana

# 启动服务
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

## 安全配置

### SSL 证书配置

#### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 手动配置 SSL

```bash
# 创建 SSL 目录
sudo mkdir -p /etc/nginx/ssl

# 生成私钥
sudo openssl genrsa -out /etc/nginx/ssl/private.key 2048

# 生成证书签名请求
sudo openssl req -new -key /etc/nginx/ssl/private.key -out /etc/nginx/ssl/cert.csr

# 生成自签名证书
sudo openssl x509 -req -days 365 -in /etc/nginx/ssl/cert.csr -signkey /etc/nginx/ssl/private.key -out /etc/nginx/ssl/cert.pem
```

### 防火墙配置

```bash
# 安装 UFW
sudo apt install ufw

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp  # 后端 API
sudo ufw allow 3000/tcp  # 前端

# 启用防火墙
sudo ufw enable
```

### API 安全

```bash
# 设置 API 密钥
export API_SECRET_KEY=$(openssl rand -hex 32)

# 配置 CORS
export CORS_ORIGINS="https://your-domain.com,https://www.your-domain.com"

# 设置请求限制
export RATE_LIMIT="100 per hour"
```

## 数据备份

### 数据库备份

```bash
# 创建备份脚本
cat > backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份 PostgreSQL
pg_dump -h localhost -U trading_user crypto_trading > $BACKUP_DIR/crypto_trading_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/crypto_trading_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# 设置定时备份
crontab -e
# 添加以下行：
# 0 2 * * * /path/to/backup_db.sh
```

### 数据文件备份

```bash
# 创建数据备份脚本
cat > backup_data.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/data"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据目录
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /path/to/qlib/data

# 备份模型文件
tar -czf $BACKUP_DIR/models_$DATE.tar.gz /path/to/qlib/mlruns

# 删除 30 天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x backup_data.sh
```

## 性能优化

### 系统优化

```bash
# 优化内核参数
cat >> /etc/sysctl.conf << 'EOF'
# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 文件系统优化
fs.file-max = 65536
vm.swappiness = 10
EOF

# 应用配置
sudo sysctl -p
```

### 数据库优化

```bash
# PostgreSQL 优化
sudo nano /etc/postgresql/14/main/postgresql.conf

# 添加以下配置：
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# 重启 PostgreSQL
sudo systemctl restart postgresql
```

### Redis 优化

```bash
# Redis 优化
sudo nano /etc/redis/redis.conf

# 添加以下配置：
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# 重启 Redis
sudo systemctl restart redis
```

## 监控和告警

### 系统监控

```bash
# 安装系统监控工具
sudo apt install htop iotop nethogs

# 设置日志轮转
sudo nano /etc/logrotate.d/crypto-trading

# 添加以下内容：
/path/to/qlib/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

### 应用监控

```bash
# 创建健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash
# 检查后端服务
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "Backend service is down" | mail -s "Service Alert" admin@example.com
fi

# 检查数据库连接
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Database is down" | mail -s "Service Alert" admin@example.com
fi

# 检查 Redis 连接
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is down" | mail -s "Service Alert" admin@example.com
fi
EOF

chmod +x health_check.sh

# 设置定时检查
crontab -e
# 添加以下行：
# */5 * * * * /path/to/health_check.sh
```

## 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 查看服务状态
docker-compose ps

# 查看详细日志
docker-compose logs -f [service_name]

# 检查端口占用
sudo netstat -tlnp | grep :5000
```

#### 2. 数据库连接失败

```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U trading_user -d crypto_trading

# 查看数据库日志
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 3. API 请求失败

```bash
# 检查 API 状态
curl -v http://localhost:5000/health

# 查看 API 日志
tail -f logs/api.log

# 检查防火墙
sudo ufw status
```

#### 4. 前端页面无法访问

```bash
# 检查前端服务
curl http://localhost:3000

# 检查 Nginx 配置
sudo nginx -t

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

### 日志分析

```bash
# 查看系统日志
sudo journalctl -u docker -f

# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep -i error logs/*.log

# 查看访问日志
tail -f /var/log/nginx/access.log
```

## 更新和维护

### 系统更新

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker-compose pull
docker-compose up -d

# 清理旧镜像
docker system prune -a
```

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose down
docker-compose up -d
```

### 数据维护

```bash
# 清理旧数据
find /path/to/qlib/data -name "*.csv" -mtime +30 -delete

# 优化数据库
psql -h localhost -U trading_user -d crypto_trading -c "VACUUM ANALYZE;"

# 清理日志
find /path/to/qlib/logs -name "*.log" -mtime +7 -delete
```

## 生产环境建议

1. **使用 HTTPS**: 配置 SSL 证书
2. **设置监控**: 使用 Prometheus + Grafana
3. **配置告警**: 设置邮件/短信告警
4. **定期备份**: 自动化数据备份
5. **安全加固**: 配置防火墙和访问控制
6. **性能优化**: 根据负载调整配置
7. **日志管理**: 配置日志轮转和集中管理
8. **版本控制**: 使用 Git 管理代码版本
9. **测试环境**: 维护独立的测试环境
10. **文档维护**: 保持部署文档更新

---

**注意**: 生产环境部署前，请务必在测试环境充分验证所有功能。

