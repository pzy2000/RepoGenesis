# 个性化设置 API

## 功能描述

这是一个个性化设置微服务API，提供用户个性化功能管理，包括收藏、点赞和历史记录功能。该服务支持用户对内容的个性化操作记录和管理，帮助构建个性化的用户体验。

## API 定义

### 服务配置
- **监听端口**: 8082
- **基础路径**: `/api/v1`
- **内容类型**: `application/json`

### 1. 收藏管理 APIs

#### 1.1 添加收藏
- **API名称**: `POST /api/v1/favorites`
- **功能**: 用户添加内容到收藏夹
- **认证**: Bearer Token 必填
- **输入Schema**:
```json
{
  "content_id": "string (必填, 内容唯一标识)",
  "content_type": "string (必填, 内容类型: post|article|product|video)",
  "category": "string (可选, 收藏分类标签)"
}
```
- **输出Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "content_id": "string",
  "content_type": "string",
  "category": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### 1.2 获取收藏列表
- **API名称**: `GET /api/v1/favorites`
- **功能**: 获取用户收藏列表，支持分页和筛选
- **认证**: Bearer Token 必填
- **查询参数**:
  - `page`: integer (默认1)
  - `limit`: integer (默认10, 最大100)
  - `content_type`: string (筛选内容类型)
  - `category`: string (筛选分类标签)
- **输出Schema**:
```json
{
  "favorites": [
    {
      "id": "string",
      "content_id": "string",
      "content_type": "string",
      "category": "string",
      "created_at": "string",
      "content_info": {
        "title": "string",
        "summary": "string",
        "thumbnail": "string"
      }
    }
  ],
  "pagination": {
    "page": "integer",
    "limit": "integer",
    "total": "integer",
    "pages": "integer"
  }
}
```

#### 1.3 删除收藏
- **API名称**: `DELETE /api/v1/favorites/{favorite_id}`
- **功能**: 删除指定收藏记录
- **认证**: Bearer Token 必填
- **输出Schema**:
```json
{
  "message": "string"
}
```

### 2. 点赞管理 APIs

#### 2.1 添加点赞
- **API名称**: `POST /api/v1/likes`
- **功能**: 用户对内容进行点赞操作
- **认证**: Bearer Token 必填
- **输入Schema**:
```json
{
  "content_id": "string (必填, 内容唯一标识)",
  "content_type": "string (必填, 内容类型: post|article|product|video)",
  "action": "string (必填, like|unlike)"
}
```
- **输出Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "content_id": "string",
  "content_type": "string",
  "action": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

#### 2.2 获取点赞统计
- **API名称**: `GET /api/v1/likes/stats/{content_id}`
- **功能**: 获取指定内容的点赞统计信息
- **认证**: 可选
- **输出Schema**:
```json
{
  "content_id": "string",
  "content_type": "string",
  "total_likes": "integer",
  "total_unlikes": "integer",
  "user_action": "string (当前用户的点赞状态: like|unlike|null)"
}
```

#### 2.3 获取用户点赞历史
- **API名称**: `GET /api/v1/likes/history`
- **功能**: 获取用户点赞历史记录
- **认证**: Bearer Token 必填
- **查询参数**:
  - `page`: integer (默认1)
  - `limit`: integer (默认10, 最大50)
  - `content_type`: string (筛选内容类型)
- **输出Schema**:
```json
{
  "likes": [
    {
      "id": "string",
      "content_id": "string",
      "content_type": "string",
      "action": "string",
      "created_at": "string"
    }
  ],
  "pagination": {
    "page": "integer",
    "limit": "integer",
    "total": "integer",
    "pages": "integer"
  }
}
```

### 3. 历史记录 APIs

#### 3.1 记录用户操作
- **API名称**: `POST /api/v1/history`
- **功能**: 记录用户的操作历史
- **认证**: Bearer Token 必填
- **输入Schema**:
```json
{
  "action": "string (必填, 操作类型: view|search|share|download)",
  "content_id": "string (可选, 相关内容ID)",
  "content_type": "string (可选, 内容类型)",
  "metadata": "object (可选, 额外信息)",
  "session_id": "string (可选, 会话标识)"
}
```
- **输出Schema**:
```json
{
  "id": "string",
  "user_id": "string",
  "action": "string",
  "content_id": "string",
  "content_type": "string",
  "metadata": "object",
  "session_id": "string",
  "created_at": "string (ISO 8601)",
  "ip_address": "string",
  "user_agent": "string"
}
```

#### 3.2 获取历史记录
- **API名称**: `GET /api/v1/history`
- **功能**: 获取用户历史记录，支持多种筛选条件
- **认证**: Bearer Token 必填
- **查询参数**:
  - `page`: integer (默认1)
  - `limit`: integer (默认20, 最大100)
  - `action`: string (筛选操作类型)
  - `content_type`: string (筛选内容类型)
  - `start_date`: string (开始日期, ISO 8601)
  - `end_date`: string (结束日期, ISO 8601)
  - `session_id`: string (筛选会话)
- **输出Schema**:
```json
{
  "history": [
    {
      "id": "string",
      "action": "string",
      "content_id": "string",
      "content_type": "string",
      "metadata": "object",
      "created_at": "string",
      "content_info": {
        "title": "string",
        "summary": "string"
      }
    }
  ],
  "pagination": {
    "page": "integer",
    "limit": "integer",
    "total": "integer",
    "pages": "integer"
  }
}
```

#### 3.3 删除历史记录
- **API名称**: `DELETE /api/v1/history/{history_id}`
- **功能**: 删除指定历史记录
- **认证**: Bearer Token 必填
- **输出Schema**:
```json
{
  "message": "string"
}
```

#### 3.4 清空历史记录
- **API名称**: `DELETE /api/v1/history`
- **功能**: 清空用户所有历史记录
- **认证**: Bearer Token 必填
- **输出Schema**:
```json
{
  "message": "string",
  "deleted_count": "integer"
}
```

## 错误响应格式

所有API在发生错误时返回统一格式：
```json
{
  "error": "string",
  "message": "string",
  "details": "object (可选)"
}
```

常见HTTP状态码：
- 200: 成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 422: 数据验证失败
- 429: 请求过于频繁
- 500: 内部服务器错误


## 测试用例

测试用例位于 `tests/` 目录下，包含：

1. **收藏功能测试** (`test_favorites_api.py`)
   - 收藏的增删改查操作
   - 收藏分类管理
   - 数据验证和错误处理

2. **点赞功能测试** (`test_likes_api.py`)
   - 点赞/取消点赞操作
   - 点赞统计查询
   - 用户点赞历史

3. **历史记录测试** (`test_history_api.py`)
   - 操作历史记录
   - 历史查询和筛选
   - 历史清理功能

## 项目结构

```
├── app/                          # 主应用代码
│   ├── api/                      # API路由定义
│   ├── core/                     # 核心配置和依赖
│   ├── models/                   # 数据模型
│   ├── services/                 # 业务逻辑服务
│   ├── utils/                    # 工具函数
│   └── main.py                   # 应用入口文件
├── tests/                        # 测试文件
│   ├── test_favorites_api.py     # 收藏API测试
│   ├── test_likes_api.py        # 点赞API测试
│   └── test_history_api.py       # 历史记录API测试
├── requirements.txt              # 项目依赖
├── start.sh                      # 启动脚本
├── Dockerfile                    # Docker镜像构建文件
├── test_startup.py               # 启动测试脚本
└── README_PROJECT.md             # 详细项目文档
```

## 快速开始

### 使用启动脚本（推荐）

```bash
# 给启动脚本添加执行权限
chmod +x start.sh

# 启动服务
./start.sh
```

启动脚本会：
1. 检查Python环境
2. 创建虚拟环境（如需要）
3. 安装依赖
4. 检查端口占用
5. 启动服务

### 手动启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

### Docker部署

```bash
# 构建镜像
docker build -t customization-api .

# 运行容器
docker run -d -p 8082:8082 --name customization-api customization-api
```

## API文档

服务启动后，可通过以下地址访问：

- **交互式API文档**: http://localhost:8082/docs
- **API模式定义**: http://localhost:8082/openapi.json
- **健康检查**: http://localhost:8082/health

## 开发指南

查看 `README_PROJECT.md` 获取详细的开发指南，包括：
- 项目结构说明
- API使用示例
- 部署指南
- 故障排除
- 贡献指南
