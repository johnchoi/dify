# Dify 本地代码构建部署指南

## 概述

此配置已修改为使用本地代码构建 Docker 镜像，而不是使用预构建的镜像。这样可以让您使用最新的本地代码进行开发和测试。

## 修改内容

已将以下服务从使用预构建镜像改为本地构建：

1. **API 服务** (`api`): 从 `../api` 目录构建
2. **Worker 服务** (`worker`): 从 `../api` 目录构建  
3. **Web 服务** (`web`): 从 `../web` 目录构建

## 使用方法

### 1. 构建并启动服务

```bash
# 进入 docker 目录
cd docker

# 构建并启动所有服务
docker-compose up --build

# 或者在后台运行
docker-compose up --build -d
```

### 2. 仅构建镜像（不启动）

```bash
# 构建所有服务的镜像
docker-compose build

# 构建特定服务的镜像
docker-compose build api
docker-compose build web
docker-compose build worker
```

### 3. 重新构建特定服务

```bash
# 重新构建并重启 API 服务
docker-compose up --build api

# 重新构建并重启 Web 服务
docker-compose up --build web
```

## 注意事项

1. **首次构建时间**: 由于需要从源代码构建镜像，首次启动时间会比使用预构建镜像更长。

2. **代码更新**: 当您修改了 `api/` 或 `web/` 目录中的代码后，需要重新构建相应的镜像：
   ```bash
   docker-compose build api  # API 代码更新后
   docker-compose build web  # Web 代码更新后
   ```

3. **依赖更新**: 如果您修改了依赖文件（如 `requirements.txt` 或 `package.json`），建议使用 `--no-cache` 选项重新构建：
   ```bash
   docker-compose build --no-cache api
   docker-compose build --no-cache web
   ```

4. **磁盘空间**: 本地构建会占用更多磁盘空间，定期清理不用的镜像：
   ```bash
   docker system prune -f
   docker image prune -f
   ```

## 构建配置

### API/Worker 服务
- **构建上下文**: `../api`
- **Dockerfile**: `../api/Dockerfile`
- **说明**: API 和 Worker 服务使用相同的镜像，通过环境变量 `MODE` 区分运行模式

### Web 服务
- **构建上下文**: `../web`
- **Dockerfile**: `../web/Dockerfile`
- **说明**: 前端 Web 应用程序

## 恢复到预构建镜像

如果需要恢复到使用预构建镜像，可以：

1. 修改 `docker-compose-template.yaml` 文件，将 `build` 配置改回 `image` 配置
2. 重新运行生成脚本：`python3 generate_docker_compose`

## 故障排除

### 构建失败
- 检查 Dockerfile 是否存在
- 确保有足够的磁盘空间
- 检查网络连接（下载依赖时）

### 服务启动失败
- 查看日志：`docker-compose logs <service_name>`
- 检查环境变量配置
- 确保所有依赖服务（数据库、Redis等）正常运行

### 性能问题
- 考虑增加 Docker 的内存和 CPU 限制
- 使用 `.dockerignore` 文件排除不必要的文件
- 优化 Dockerfile 中的层缓存 
