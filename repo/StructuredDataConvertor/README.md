# StructuredDataConvertor

StructuredDataConvertor is a web application that provides data format conversion services, supporting bidirectional conversion between Excel, CSV, and PDF formats.

## Description

This project provides the following core features:

1. **Data Format Conversion**: Supports bidirectional conversion between Excel, CSV, and PDF formats.
   - Excel ↔ CSV
   - Excel ↔ PDF
   - CSV ↔ PDF

2. **Data Import and Export**: Supports importing data from various sources and exporting to specified formats.

3. **Batch Processing**: Supports batch file conversion to improve processing efficiency.

4. **Format Validation**: Performs format validation on input data to ensure conversion quality.

## API Definition

### Service Configuration
- **Listening Port**: 8000
- **Host Address**: 0.0.0.0 (supports all network interfaces)
- **API Base Path**: /api/v1

### API Specifications

#### 1. Health Check API
- **Endpoint**: `/health`
- **HTTP Method**: GET
- **Function**: Check the running status of the service

**Output Schema**:
```json
{
  "status": "string",     // Service status: "healthy" | "unhealthy"
  "timestamp": "string",  // ISO formatted timestamp
  "version": "string"     // Service version number
}
```

#### 2. Format Conversion API
- **Endpoint**: `/convert`
- **HTTP Method**: POST
- **Function**: Execute data format conversion

**Input Schema**:
```json
{
  "source_format": "string",     // Source format: "excel" | "csv" | "pdf"
  "target_format": "string",     // Target format: "excel" | "csv" | "pdf"
  "data": "string",             // Data to convert (base64 encoded source file content)
  "options": {                  // Conversion options (optional)
    "encoding": "string",       // File encoding, default "utf-8"
    "delimiter": "string",      // CSV delimiter, default ","
    "has_header": "boolean",    // Whether to include header, default true
    "sheet_name": "string"      // Excel sheet name, default "Sheet1"
  }
}
```

**Output Schema**:
```json
{
  "success": "boolean",          // Whether conversion was successful
  "message": "string",          // Status message
  "result": "string",           // Conversion result (base64 encoded target file content)
  "metadata": {                 // Metadata information
    "source_size": "integer",   // Source file size (bytes)
    "target_size": "integer",   // Target file size (bytes)
    "conversion_time": "float", // Conversion time (seconds)
    "rows_count": "integer",    // Number of data rows
    "columns_count": "integer"  // Number of data columns
  }
}
```

#### 3. Batch Conversion API
- **Endpoint**: `/convert/batch`
- **HTTP Method**: POST
- **Function**: Execute batch data format conversion

**Input Schema**:
```json
{
  "conversions": [              // List of conversion tasks
    {
      "source_format": "string",
      "target_format": "string",
      "data": "string",
      "options": {...}
    }
  ],
  "parallel": "boolean"         // Whether to process in parallel, default false
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "results": [                  // List of conversion results, matching input order
    {
      "success": "boolean",
      "message": "string",
      "result": "string",
      "metadata": {...}
    }
  ],
  "summary": {                  // Batch processing summary
    "total_count": "integer",   // Total number of tasks
    "success_count": "integer", // Number of successful tasks
    "failure_count": "integer", // Number of failed tasks
    "total_time": "float"       // Total time (seconds)
  }
}
```

## Test Case Specifications

Test cases are located in the `tests/` directory, using the following naming conventions:
- `test_health.py` - Health check API tests
- `test_convert.py` - Single conversion API tests
- `test_convert_batch.py` - Batch conversion API tests
- `test_performance.py` - Performance tests
- `test_integration.py` - Integration tests

## Usage Examples

### Start the Service
```bash
python main.py
```

The service will start at http://localhost:8000

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Single Conversion Example
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

### Batch Conversion Example
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

## Development Standards

- Adopt Test-Driven Development (TDD) mode
- Follow RESTful API design principles
- Use type hints and docstrings
- Keep code concise and maintainable
- Perform regular code reviews and refactoring
