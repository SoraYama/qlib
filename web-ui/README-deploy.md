# 加密货币量化交易系统部署脚本使用说明

## 概述

`deploy.sh` 是一个功能完整的部署管理脚本，支持一键启动、停止、重启和管理加密货币量化交易系统的所有服务。

## 功能特性

- ✅ **一键启动**: 自动检查依赖、创建目录、构建镜像、启动服务
- ✅ **一键停止**: 安全停止所有服务并清理容器
- ✅ **一键重启**: 停止后重新启动所有服务
- ✅ **状态监控**: 查看服务状态和资源使用情况
- ✅ **日志查看**: 实时查看所有服务日志
- ✅ **重新构建**: 清理并重新构建所有镜像
- ✅ **完全清理**: 清理所有容器、镜像和卷

## 使用方法

### 基本命令

```bash
# 启动所有服务（默认命令）
./deploy.sh start

# 停止所有服务
./deploy.sh stop

# 重启所有服务
./deploy.sh restart

# 查看服务状态
./deploy.sh status

# 查看实时日志
./deploy.sh logs

# 重新构建并启动服务
./deploy.sh build

# 清理所有容器和镜像
./deploy.sh clean

# 显示帮助信息
./deploy.sh help
```

### 使用示例

```bash
# 首次部署
./deploy.sh start

# 查看服务是否正常运行
./deploy.sh status

# 如果出现问题，重启服务
./deploy.sh restart

# 查看日志排查问题
./deploy.sh logs

# 更新代码后重新构建
./deploy.sh build

# 完全清理环境
./deploy.sh clean
```

## 服务启动顺序

脚本会按以下顺序启动服务，确保依赖关系正确：

1. **基础服务**: Redis, PostgreSQL
2. **后端服务**: API 服务器
3. **前端服务**: Web 界面
4. **代理服务**: Nginx 反向代理
5. **数据采集**: 数据采集服务

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 配置说明

### 环境变量文件

脚本会自动检查 `.env` 文件，如果不存在会从 `env.example` 复制模板。

**重要配置项**:
- `GATE_API_KEY`: Gate.io API 密钥
- `GATE_API_SECRET`: Gate.io API 密钥
- `CRYPTOPANIC_API_KEY`: CryptoPanic API 密钥

### 目录结构

脚本会自动创建以下目录：
```
logs/                    # 日志文件
data/
├── gate/
│   ├── source/         # Gate.io 原始数据
│   └── normalize/      # 标准化数据
├── news/
│   ├── source/         # 新闻原始数据
│   └── normalize/      # 标准化数据
└── onchain/
    ├── source/         # 链上原始数据
    └── normalize/      # 标准化数据
reports/                # 报告文件
ssl/                    # SSL 证书
```

## 访问地址

服务启动后可通过以下地址访问：

- **主界面**: http://localhost
- **API 文档**: http://localhost/api
- **健康检查**: http://localhost/api/health

## 故障排除

### 常见问题

1. **端口冲突**: 确保 80、443、5432、6379 端口未被占用
2. **内存不足**: 确保系统有足够内存运行所有服务
3. **权限问题**: 确保脚本有执行权限 `chmod +x deploy.sh`
4. **Docker 未启动**: 确保 Docker 服务正在运行

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
docker compose logs -f [service_name]

# 查看服务状态
./deploy.sh status
```

### 重置环境

如果遇到无法解决的问题，可以完全重置环境：

```bash
# 停止并清理所有服务
./deploy.sh clean

# 重新启动
./deploy.sh start
```

## 高级功能

### 启动特定服务

```bash
# 启动实盘交易服务
docker compose --profile trading up -d

# 启动监控服务
docker compose --profile monitoring up -d
```

### 手动管理

```bash
# 查看所有容器
docker compose ps

# 重启特定服务
docker compose restart [service_name]

# 查看服务日志
docker compose logs [service_name]

# 进入容器调试
docker compose exec [service_name] /bin/bash
```

## 注意事项

1. **首次启动**: 需要下载数据，可能需要较长时间
2. **API 密钥**: 请确保已正确配置所有必要的 API 密钥
3. **实盘交易**: 默认关闭，需要手动启用
4. **测试环境**: 建议先在测试环境验证系统功能
5. **数据备份**: 定期备份重要数据
6. **安全更新**: 定期更新系统和依赖包

## 技术支持

如果遇到问题，请：

1. 查看日志文件排查问题
2. 检查系统资源使用情况
3. 验证配置文件是否正确
4. 确认网络连接正常
5. 联系技术支持团队
