# Mail Notification Service

## Overview

Mail Notification Service is a RESTful web service for sending and managing email notifications. The service provides APIs for sending single or batch emails, checking email status, and retrieving email history.

## Service Configuration

- **Port**: 8080
- **Base URL**: `http://localhost:8080`
- **API Version**: v1

## API Endpoints

### 1. Send Single Email

**Endpoint**: `POST /api/v1/mail/send`

**Description**: Send a single email to one or more recipients.

**Input Schema**:
```json
{
  "to": ["string"],          // Required: List of recipient email addresses
  "subject": "string",       // Required: Email subject
  "body": "string",          // Required: Email body content
  "from": "string",          // Optional: Sender email address (default: system email)
  "cc": ["string"],          // Optional: CC recipients
  "bcc": ["string"],         // Optional: BCC recipients
  "priority": "string"       // Optional: Email priority (low, normal, high), default: normal
}
```

**Output Schema**:
```json
{
  "mail_id": "string",       // Unique identifier for the email
  "status": "string",        // Email status: pending, sent, failed
  "message": "string",       // Status message
  "timestamp": "string"      // ISO 8601 timestamp
}
```

**Status Codes**:
- 200: Email queued successfully
- 400: Invalid input data
- 500: Internal server error

### 2. Send Batch Emails

**Endpoint**: `POST /api/v1/mail/send-batch`

**Description**: Send multiple emails in a single request.

**Input Schema**:
```json
{
  "emails": [
    {
      "to": ["string"],
      "subject": "string",
      "body": "string",
      "from": "string",
      "cc": ["string"],
      "bcc": ["string"],
      "priority": "string"
    }
  ]
}
```

**Output Schema**:
```json
{
  "batch_id": "string",      // Unique identifier for the batch
  "total": "integer",        // Total number of emails in batch
  "queued": "integer",       // Number of emails successfully queued
  "failed": "integer",       // Number of emails that failed
  "results": [
    {
      "mail_id": "string",
      "status": "string",
      "message": "string"
    }
  ],
  "timestamp": "string"
}
```

**Status Codes**:
- 200: Batch processed (check individual results for status)
- 400: Invalid input data
- 500: Internal server error

### 3. Get Email Status

**Endpoint**: `GET /api/v1/mail/status/{mail_id}`

**Description**: Retrieve the current status of a sent email.

**Path Parameters**:
- `mail_id` (string, required): The unique identifier of the email

**Output Schema**:
```json
{
  "mail_id": "string",
  "status": "string",        // pending, sent, failed, delivered, bounced
  "to": ["string"],
  "subject": "string",
  "sent_at": "string",       // ISO 8601 timestamp
  "delivered_at": "string",  // ISO 8601 timestamp (null if not delivered)
  "error": "string"          // Error message (null if no error)
}
```

**Status Codes**:
- 200: Status retrieved successfully
- 404: Email not found
- 500: Internal server error

### 4. Get Email History

**Endpoint**: `GET /api/v1/mail/history`

**Description**: Retrieve email sending history with optional filters.

**Query Parameters**:
- `limit` (integer, optional): Maximum number of records to return (default: 50, max: 100)
- `offset` (integer, optional): Number of records to skip (default: 0)
- `status` (string, optional): Filter by status (pending, sent, failed, delivered, bounced)
- `from_date` (string, optional): Filter emails sent after this date (ISO 8601)
- `to_date` (string, optional): Filter emails sent before this date (ISO 8601)

**Output Schema**:
```json
{
  "total": "integer",        // Total number of records matching filters
  "limit": "integer",
  "offset": "integer",
  "emails": [
    {
      "mail_id": "string",
      "to": ["string"],
      "subject": "string",
      "status": "string",
      "sent_at": "string",
      "delivered_at": "string"
    }
  ]
}
```

**Status Codes**:
- 200: History retrieved successfully
- 400: Invalid query parameters
- 500: Internal server error

## Email Status Flow

1. **pending**: Email is queued and waiting to be sent
2. **sent**: Email has been sent to the mail server
3. **delivered**: Email has been successfully delivered to recipient
4. **failed**: Email sending failed
5. **bounced**: Email was rejected by recipient server

## Error Codes

All error responses follow this schema:
```json
{
  "error": "string",         // Error code
  "message": "string",       // Human-readable error message
  "details": "object"        // Optional: Additional error details
}
```

Common error codes:
- `INVALID_EMAIL`: Invalid email address format
- `MISSING_FIELD`: Required field is missing
- `INVALID_PRIORITY`: Invalid priority value
- `BATCH_TOO_LARGE`: Batch size exceeds limit (max 100 emails per batch)
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Internal server error

## Requirements

- All email addresses must be valid according to RFC 5322
- Email body size limit: 1MB
- Batch size limit: 100 emails per request
- Rate limit: 100 requests per minute per client

## Dependencies

- Python 3.8+
- FastAPI or Flask (web framework)
- pytest (testing framework)

