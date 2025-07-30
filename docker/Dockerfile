FROM redis:7-alpine

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# 安装Python和系统依赖
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    python3-dev

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装Python依赖
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]