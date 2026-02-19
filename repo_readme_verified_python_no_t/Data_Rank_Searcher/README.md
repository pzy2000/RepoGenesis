# Data Rank Searcher

## 功能描述

Data Rank Searcher 是一个支持分页、排序、搜索和模糊查询的数据管理服务。该服务提供 RESTful API 接口，用于管理数据记录并支持灵活的查询功能。

### 核心功能

1. **数据管理**：添加、查询、删除数据记录
2. **分页功能**：支持按页码和每页数量进行数据分页
3. **排序功能**：支持按指定字段进行升序或降序排序
4. **精确搜索**：支持按字段精确匹配查询
5. **模糊查询**：支持按字段进行模糊匹配查询

## 接口定义

### 服务配置

- **监听端口**：8080
- **Base URL**：`http://localhost:8080`

### API 接口

#### 1. 添加数据记录

- **接口名称**：`POST /api/data`
- **功能描述**：添加一条新的数据记录
- **Input Schema**：
```json
{
  "name": "string (required)",
  "category": "string (required)",
  "score": "number (required)",
  "description": "string (optional)",
  "tags": "array of strings (optional)"
}
```
- **Output Schema**：
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "id": "string",
    "name": "string",
    "category": "string",
    "score": "number",
    "description": "string",
    "tags": "array of strings",
    "created_at": "string (ISO 8601 format)"
  }
}
```

#### 2. 查询数据记录

- **接口名称**：`GET /api/data`
- **功能描述**：查询数据记录，支持分页、排序、搜索和模糊查询
- **Query Parameters**：
  - `page`: 页码，从 1 开始（默认：1）
  - `page_size`: 每页数量（默认：10，最大：100）
  - `sort_by`: 排序字段（可选值：name, category, score, created_at）
  - `sort_order`: 排序顺序（可选值：asc, desc，默认：asc）
  - `search_field`: 精确搜索字段名
  - `search_value`: 精确搜索值
  - `fuzzy_field`: 模糊查询字段名
  - `fuzzy_value`: 模糊查询值
- **Output Schema**：
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "category": "string",
        "score": "number",
        "description": "string",
        "tags": "array of strings",
        "created_at": "string"
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number"
    }
  }
}
```

#### 3. 获取单条数据记录

- **接口名称**：`GET /api/data/{id}`
- **功能描述**：根据 ID 获取单条数据记录
- **Path Parameters**：
  - `id`: 数据记录 ID
- **Output Schema**：
```json
{
  "success": "boolean",
  "message": "string",
  "data": {
    "id": "string",
    "name": "string",
    "category": "string",
    "score": "number",
    "description": "string",
    "tags": "array of strings",
    "created_at": "string"
  }
}
```

#### 4. 删除数据记录

- **接口名称**：`DELETE /api/data/{id}`
- **功能描述**：根据 ID 删除数据记录
- **Path Parameters**：
  - `id`: 数据记录 ID
- **Output Schema**：
```json
{
  "success": "boolean",
  "message": "string"
}
```

## 实现要求

1. 服务应能正确处理所有定义的接口
2. 所有响应应符合定义的 Schema
3. 支持并发请求处理
4. 错误处理应返回合适的 HTTP 状态码和错误信息
5. 数据持久化（可使用内存存储或数据库）

## 测试说明

测试用例位于 `tests/` 目录下，所有测试均为真实的接口测试，不使用 mock。测试前需确保服务已启动并监听在 8080 端口。

