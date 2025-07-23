# base image
FROM python:3.12-slim-bookworm AS base

WORKDIR /app/api

# Install uv
ENV UV_VERSION=0.7.11

RUN pip install --no-cache-dir --default-timeout=100 -i https://pypi.tuna.tsinghua.edu.cn/simple uv==${UV_VERSION}


FROM base AS packages

# if you located in China, you can use aliyun mirror to speed up
# RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

# 创建sources.list文件
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-backports main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security/ bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 更新系统并安装编译依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc-dev \
        libffi-dev \
        libgmp-dev \
        libmpfr-dev \
        libmpc-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml uv.lock ./

# Set UV environment variables for better network handling
ENV UV_HTTP_TIMEOUT=300
ENV UV_CONCURRENT_DOWNLOADS=1
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN uv sync

# production stage
FROM base AS production

ENV FLASK_APP=app.py
ENV EDITION=SELF_HOSTED
ENV DEPLOY_ENV=PRODUCTION
ENV CONSOLE_API_URL=http://127.0.0.1:5001
ENV CONSOLE_WEB_URL=http://127.0.0.1:3000
ENV SERVICE_API_URL=http://127.0.0.1:5001
ENV APP_WEB_URL=http://127.0.0.1:3000

EXPOSE 5001

# set timezone
ENV TZ=UTC

WORKDIR /app/api

# 配置国内镜像源以加速包下载
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-backports main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security/ bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 配置 apt 加速选项
RUN echo 'Acquire::http::timeout "10";' > /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::ftp::timeout "10";' >> /etc/apt/apt.conf.d/99timeout && \
    echo 'Acquire::Retries "3";' >> /etc/apt/apt.conf.d/99timeout && \
    echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf.d/99timeout && \
    echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/99timeout

RUN \
    apt-get update \
    # Install dependencies
    && apt-get install -y --no-install-recommends \
        # basic environment
        curl nodejs libgmp-dev libmpfr-dev libmpc-dev \
        # For Security
        expat libldap-2.5-0 perl libsqlite3-0 zlib1g \
        # install fonts to support the use of tools like pypdfium2
        fonts-noto-cjk \
        # install a package to improve the accuracy of guessing mime type and file extension
        media-types \
        # install libmagic to support the use of python-magic guess MIMETYPE
        libmagic1 \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment and packages
ENV VIRTUAL_ENV=/app/api/.venv
COPY --from=packages ${VIRTUAL_ENV} ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# 配置 NLTK 数据下载环境变量（使用国内镜像和优化设置）
ENV NLTK_DATA=/app/api/nltk_data
ENV NLTK_DATA_TIMEOUT=60

# 复制 NLTK 下载脚本
COPY docker/download_nltk_data.py /tmp/download_nltk_data.py

# 下载 NLTK 数据 - 使用优化脚本和重试机制
RUN mkdir -p ${NLTK_DATA} && \
    if [ -f /tmp/docker_files/nltk_data.tar.gz ]; then \
        echo "🎉 发现预下载的 NLTK 数据包，正在解压..."; \
        tar -xzf /tmp/docker_files/nltk_data.tar.gz -C ${NLTK_DATA}; \
        echo "✅ NLTK 离线数据包安装完成"; \
    else \
        echo "⚠️  未找到离线数据包，使用在线下载方式..."; \
        python -c "import nltk; import ssl; import os; \
        ssl._create_default_https_context = ssl._create_unverified_context; \
        os.environ['PYTHONHTTPSVERIFY'] = '0'; \
        print('🔄 开始下载 NLTK 数据...'); \
        print('下载 punkt...'); \
        try: nltk.download('punkt', download_dir='${NLTK_DATA}', timeout=120); print('✅ punkt 下载成功'); except Exception as e: print(f'❌ punkt 下载失败: {e}'); \
        print('下载 averaged_perceptron_tagger...'); \
        try: nltk.download('averaged_perceptron_tagger', download_dir='${NLTK_DATA}', timeout=120); print('✅ tagger 下载成功'); except Exception as e: print(f'❌ tagger 下载失败: {e}')"; \
    fi && \
    rm -rf /tmp/docker_files

ENV TIKTOKEN_CACHE_DIR=/app/api/.tiktoken_cache

RUN python -c "import tiktoken; tiktoken.encoding_for_model('gpt2')"

# Copy source code
COPY . /app/api/

# Copy entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
