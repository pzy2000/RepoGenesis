# Timer4Tasker - 定时任务管理系统

## 项目概述

Timer4Tasker 是一个轻量级的定时任务管理系统，提供 RESTful API 接口用于创建、管理和执行定时任务。系统支持多种类型的定时任务，包括文件清理、数据汇总和数据备份等。

## 功能描述

### 核心功能

1. **定时任务管理**
   - 创建定时任务
   - 查询任务列表
   - 查询任务详情
   - 更新任务配置
   - 删除任务
   - 启动/停止任务

2. **任务类型**
   - 文件清理任务：定期清理指定目录下的过期文件
   - 数据汇总任务：定期对数据进行统计和汇总
   - 数据备份任务：定期备份指定的数据

3. **任务执行记录**
   - 查询任务执行历史
   - 查询任务执行状态
   - 获取任务执行结果

## API 接口定义

### 服务配置

- **监听端口**: 8080
- **Base URL**: `http://localhost:8080/api/v1`
- **Content-Type**: `application/json`

### 接口列表

#### 1. 创建定时任务

**接口**: `POST /tasks`

**Input Schema**:
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "task_type": "string (required, enum: ['file_cleanup', 'data_summary', 'data_backup'])",
  "schedule": "string (required, cron expression)",
  "config": {
    "path": "string (optional, for file_cleanup)",
    "pattern": "string (optional, for file_cleanup)",
    "days": "integer (optional, for file_cleanup)",
    "source": "string (optional, for data_summary/data_backup)",
    "target": "string (optional, for data_backup)"
  },
  "enabled": "boolean (optional, default: true)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "task_type": "string",
    "schedule": "string",
    "enabled": "boolean",
    "created_at": "string (ISO 8601 format)"
  },
  "message": "string (optional)"
}
```

#### 2. 获取任务列表

**接口**: `GET /tasks`

**Query Parameters**:
- `task_type`: string (optional, filter by task type)
- `enabled`: boolean (optional, filter by enabled status)
- `page`: integer (optional, default: 1)
- `page_size`: integer (optional, default: 10)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "tasks": [
      {
        "task_id": "string",
        "name": "string",
        "task_type": "string",
        "schedule": "string",
        "enabled": "boolean",
        "created_at": "string",
        "last_run": "string (optional)"
      }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
  },
  "message": "string (optional)"
}
```

#### 3. 获取任务详情

**接口**: `GET /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "description": "string",
    "task_type": "string",
    "schedule": "string",
    "config": "object",
    "enabled": "boolean",
    "created_at": "string",
    "updated_at": "string",
    "last_run": "string (optional)",
    "next_run": "string (optional)"
  },
  "message": "string (optional)"
}
```

#### 4. 更新任务

**接口**: `PUT /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Input Schema**:
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "schedule": "string (optional)",
  "config": "object (optional)",
  "enabled": "boolean (optional)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "name": "string",
    "task_type": "string",
    "schedule": "string",
    "enabled": "boolean",
    "updated_at": "string"
  },
  "message": "string (optional)"
}
```

#### 5. 删除任务

**接口**: `DELETE /tasks/{task_id}`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "message": "string"
}
```

#### 6. 启动/停止任务

**接口**: `POST /tasks/{task_id}/toggle`

**Path Parameters**:
- `task_id`: string (required)

**Input Schema**:
```json
{
  "enabled": "boolean (required)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "task_id": "string",
    "enabled": "boolean"
  },
  "message": "string (optional)"
}
```

#### 7. 手动执行任务

**接口**: `POST /tasks/{task_id}/execute`

**Path Parameters**:
- `task_id`: string (required)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "execution_id": "string",
    "task_id": "string",
    "status": "string (enum: ['running', 'completed', 'failed'])",
    "started_at": "string"
  },
  "message": "string (optional)"
}
```

#### 8. 获取任务执行历史

**接口**: `GET /tasks/{task_id}/executions`

**Path Parameters**:
- `task_id`: string (required)

**Query Parameters**:
- `limit`: integer (optional, default: 20)

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "executions": [
      {
        "execution_id": "string",
        "task_id": "string",
        "status": "string",
        "started_at": "string",
        "completed_at": "string (optional)",
        "result": "object (optional)",
        "error": "string (optional)"
      }
    ]
  },
  "message": "string (optional)"
}
```

#### 9. 获取系统统计信息

**接口**: `GET /stats`

**Output Schema**:
```json
{
  "success": "boolean",
  "data": {
    "total_tasks": "integer",
    "active_tasks": "integer",
    "total_executions": "integer",
    "successful_executions": "integer",
    "failed_executions": "integer"
  },
  "message": "string (optional)"
}
```

## 错误码说明

| HTTP Status Code | 说明 |
|-----------------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 技术要求

1. 使用 Python 3.8+ 开发
2. 使用 FastAPI 或 Flask 框架构建 Web 服务
3. 使用 APScheduler 或 Celery 实现定时任务调度
4. 数据持久化使用 SQLite 或其他数据库
5. 提供完整的单元测试和集成测试

## 部署说明

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 服务将在 http://localhost:8080 启动
```

## 测试说明

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_task_management.py

# 查看测试覆盖率
pytest --cov=. tests/
```

