# StructuredDataConvertor

结构化数据转换器是一个提供数据格式转换服务的Web应用程序，支持Excel、CSV和PDF格式之间的互相转换。

## 功能描述

本项目提供以下核心功能：

1. **数据格式转换**：支持在Excel、CSV、PDF格式之间进行双向转换
   - Excel ↔ CSV
   - Excel ↔ PDF
   - CSV ↔ PDF

2. **数据导入导出**：支持从各种数据源导入数据并导出为指定格式

3. **批量处理**：支持批量文件转换，提高处理效率

4. **格式验证**：对输入数据进行格式验证，确保转换质量

## 接口定义

### 服务配置
- **监听端口**：8000
- **主机地址**：0.0.0.0 (支持所有网络接口)
- **API基础路径**：/api/v1

### API接口规范

#### 1. 健康检查接口
- **接口名**：`/health`
- **HTTP方法**：GET
- **功能**：检查服务运行状态

**输出Schema**:
```json
{
  "status": "string",     // 服务状态: "healthy" | "unhealthy"
  "timestamp": "string",  // ISO格式时间戳
  "version": "string"     // 服务版本号
}
```

#### 2. 格式转换接口
- **接口名**：`/convert`
- **HTTP方法**：POST
- **功能**：执行数据格式转换

**输入Schema**:
```json
{
  "source_format": "string",     // 源格式: "excel" | "csv" | "pdf"
  "target_format": "string",     // 目标格式: "excel" | "csv" | "pdf"
  "data": "string",             // 转换数据 (base64编码的源文件内容)
  "options": {                  // 转换选项 (可选)
    "encoding": "string",       // 文件编码, 默认"utf-8"
    "delimiter": "string",      // CSV分隔符, 默认","
    "has_header": "boolean",    // 是否包含表头, 默认true
    "sheet_name": "string"      // Excel工作表名, 默认"Sheet1"
  }
}
```

**输出Schema**:
```json
{
  "success": "boolean",          // 转换是否成功
  "message": "string",          // 状态消息
  "result": "string",           // 转换结果 (base64编码的目标文件内容)
  "metadata": {                 // 元数据信息
    "source_size": "integer",   // 源文件大小(字节)
    "target_size": "integer",   // 目标文件大小(字节)
    "conversion_time": "float", // 转换耗时(秒)
    "rows_count": "integer",    // 数据行数
    "columns_count": "integer"  // 数据列数
  }
}
```

#### 3. 批量转换接口
- **接口名**：`/convert/batch`
- **HTTP方法**：POST
- **功能**：批量执行数据格式转换

**输入Schema**:
```json
{
  "conversions": [              // 转换任务列表
    {
      "source_format": "string",
      "target_format": "string",
      "data": "string",
      "options": {...}
    }
  ],
  "parallel": "boolean"         // 是否并行处理, 默认false
}
```

**输出Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "results": [                  // 转换结果列表，与输入顺序对应
    {
      "success": "boolean",
      "message": "string",
      "result": "string",
      "metadata": {...}
    }
  ],
  "summary": {                  // 批量处理汇总
    "total_count": "integer",   // 总任务数
    "success_count": "integer", // 成功任务数
    "failure_count": "integer", // 失败任务数
    "total_time": "float"       // 总耗时(秒)
  }
}
```

## 测试用例规范

测试用例位于`tests/`目录下，采用以下命名约定：
- `test_health.py` - 健康检查接口测试
- `test_convert.py` - 单次转换接口测试
- `test_convert_batch.py` - 批量转换接口测试
- `test_performance.py` - 性能测试
- `test_integration.py` - 集成测试


## 使用示例

### 启动服务
```bash
python main.py
```

服务将在 http://localhost:8000 启动

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

### 单次转换示例
```bash
curl -X POST http://localhost:8000/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_format": "csv",
    "target_format": "excel",
    "data": "base64_encoded_csv_data",
    "options": {
      "encoding": "utf-8",
      "has_header": true
    }
  }'
```

### 批量转换示例
```bash
curl -X POST http://localhost:8000/api/v1/convert/batch \
  -H "Content-Type: application/json" \
  -d '{
    "conversions": [
      {
        "source_format": "csv",
        "target_format": "excel",
        "data": "base64_csv_data_1"
      },
      {
        "source_format": "excel",
        "target_format": "pdf",
        "data": "base64_excel_data_2"
      }
    ],
    "parallel": true
  }'
```

## 开发规范

- 采用测试驱动开发(TDD)模式
- 遵循RESTful API设计原则
- 使用类型提示和文档字符串
- 保持代码简洁和可维护性
- 定期进行代码审查和重构

