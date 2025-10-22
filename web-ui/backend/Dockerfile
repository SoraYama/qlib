FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括git和编译工具）
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY web-ui/backend/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装qlib及其依赖
RUN pip install --no-cache-dir pyqlib redis dill python-redis-lock pymongo cvxpy empyrical-reloaded pydantic-settings gym

# 覆盖qlib的cli和contrib模块（使用本地版本）
COPY qlib/cli /usr/local/lib/python3.9/site-packages/qlib/cli
COPY qlib/contrib /usr/local/lib/python3.9/site-packages/qlib/contrib
COPY qlib/workflow /usr/local/lib/python3.9/site-packages/qlib/workflow
COPY qlib/model /usr/local/lib/python3.9/site-packages/qlib/model
COPY qlib/data /usr/local/lib/python3.9/site-packages/qlib/data
COPY qlib/backtest /usr/local/lib/python3.9/site-packages/qlib/backtest
COPY qlib/strategy /usr/local/lib/python3.9/site-packages/qlib/strategy
COPY qlib/utils /usr/local/lib/python3.9/site-packages/qlib/utils
COPY qlib/config.py /usr/local/lib/python3.9/site-packages/qlib/config.py
COPY qlib/log.py /usr/local/lib/python3.9/site-packages/qlib/log.py

# 复制custom-scripts到容器（重命名为custom_scripts以便Python导入）
COPY custom-scripts /app/custom_scripts

# 复制应用代码
COPY web-ui/backend /app

# 创建日志目录
RUN mkdir -p logs

# 设置PYTHONPATH环境变量，确保可以导入custom_scripts
ENV PYTHONPATH="/app:${PYTHONPATH}"

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动应用
CMD ["python", "app.py"]
