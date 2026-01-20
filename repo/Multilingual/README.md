# Multilingual and Multi-Timezone Support Service

## Project Overview

This project provides a simple web service that handles multilingual text translation and timezone conversions. The service exposes RESTful API endpoints to support internationalization features.

## Features

- Text translation between multiple languages
- Timezone conversion
- Localized datetime formatting
- Supported languages query

## Technical Requirements

- Python 3.8+
- Flask framework
- Required packages: flask, pytz, googletrans==4.0.0rc1 (or any translation library)

## Installation

```bash
pip install flask pytz googletrans==4.0.0rc1
```

## Running the Service

```bash
python app.py
```

The service will start on `http://localhost:5000`

## API Endpoints

### 1. Translate Text

**Endpoint:** `/api/translate`

**Method:** POST

**Port:** 5000

**Input Schema:**
```json
{
  "text": "string (required) - Text to translate",
  "source_lang": "string (required) - Source language code (e.g., 'en', 'zh-cn', 'es')",
  "target_lang": "string (required) - Target language code (e.g., 'en', 'zh-cn', 'es')"
}
```

**Output Schema:**
```json
{
  "success": "boolean - Operation status",
  "original_text": "string - Original text",
  "translated_text": "string - Translated text",
  "source_lang": "string - Source language",
  "target_lang": "string - Target language"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_lang": "en", "target_lang": "zh-cn"}'
```

### 2. Convert Timezone

**Endpoint:** `/api/timezone`

**Method:** POST

**Port:** 5000

**Input Schema:**
```json
{
  "datetime": "string (required) - ISO format datetime (e.g., '2025-10-30T12:00:00')",
  "from_timezone": "string (required) - Source timezone (e.g., 'UTC', 'America/New_York')",
  "to_timezone": "string (required) - Target timezone (e.g., 'Asia/Shanghai', 'Europe/London')"
}
```

**Output Schema:**
```json
{
  "success": "boolean - Operation status",
  "original_datetime": "string - Original datetime with source timezone",
  "converted_datetime": "string - Converted datetime with target timezone",
  "from_timezone": "string - Source timezone",
  "to_timezone": "string - Target timezone"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/timezone \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2025-10-30T12:00:00", "from_timezone": "UTC", "to_timezone": "Asia/Shanghai"}'
```

### 3. Get Localized DateTime

**Endpoint:** `/api/localize`

**Method:** POST

**Port:** 5000

**Input Schema:**
```json
{
  "datetime": "string (required) - ISO format datetime (e.g., '2025-10-30T12:00:00')",
  "timezone": "string (required) - Timezone (e.g., 'UTC', 'Asia/Shanghai')",
  "locale": "string (required) - Locale code (e.g., 'en_US', 'zh_CN', 'es_ES')"
}
```

**Output Schema:**
```json
{
  "success": "boolean - Operation status",
  "formatted_datetime": "string - Localized datetime string",
  "timezone": "string - Timezone used",
  "locale": "string - Locale used"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/localize \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2025-10-30T12:00:00", "timezone": "Asia/Shanghai", "locale": "zh_CN"}'
```

### 4. Get Supported Languages

**Endpoint:** `/api/languages`

**Method:** GET

**Port:** 5000

**Input Schema:** None

**Output Schema:**
```json
{
  "success": "boolean - Operation status",
  "languages": {
    "language_code": "language_name",
    "...": "..."
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/languages
```

## Metrics

### Test Case Pass Rate
- Calculated as: (Passed Tests / Total Tests) × 100%
- Each API endpoint should have multiple test cases covering:
  - Valid inputs
  - Invalid inputs
  - Edge cases
  - Error handling

### Repository Pass Rate
- Calculated as: (Repositories with All Tests Passing / Total Repositories) × 100%
- A repository passes when all its test cases pass

## Error Handling

All endpoints return error responses in the following format when requests fail:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 500: Internal Server Error

## Notes

- All datetime strings should use ISO 8601 format
- Timezone names follow the IANA Time Zone Database
- Language codes follow ISO 639-1 (two-letter codes)
- Locale codes follow the format: language_COUNTRY (e.g., en_US, zh_CN)

