# Text Moderation API Specification

## Base Configuration
```
Base URL: https://api.moderation-service.com/v1
Content-Type: application/json
```

## Authentication
All requests require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_api_token>
```

## 1. Single Text Moderation

### Endpoint: POST /api/v1/moderate/text

### Request Structure

```json
{
  "content": {
    "text": "Text content to be moderated",
    "language": "en",
    "context": {
      "domain": "social_media",
      "contentType": "comment",
      "userId": "user123",
      "parentId": "post789"
    }
  },
  "configuration": {
    "sensitivityLevel": "MEDIUM",
    "categories": ["PROFANITY", "HATE_SPEECH", "HARASSMENT"],
    "customRules": [
      {
        "ruleId": "CUSTOM_RULE_1",
        "enabled": true
      }
    ]
  },
  "metadata": {
    "clientId": "client123",
    "requestId": "req789",
    "timestamp": "2025-02-08T10:30:00Z"
  }
}
```

### Success Response (200 OK)
Clean Content:
```json
{
  "status": "SUCCESS",
  "requestId": "req789",
  "timestamp": "2025-02-08T10:30:05Z",
  "processingTime": 123,
  "result": {
    "decision": "APPROVED",
    "confidence": 0.95,
    "analysis": {
      "language": "en",
      "toxicity": 0.02,
      "sentiment": 0.6,
      "categories": {
        "PROFANITY": {
          "score": 0.01,
          "verdict": "CLEAN"
        },
        "HATE_SPEECH": {
          "score": 0.02,
          "verdict": "CLEAN"
        },
        "HARASSMENT": {
          "score": 0.01,
          "verdict": "CLEAN"
        }
      }
    },
    "metadata": {
      "processedAt": "2025-02-08T10:30:05Z",
      "modelVersion": "v2.1"
    }
  }
}
```

Flagged Content:
```json
{
  "status": "SUCCESS",
  "requestId": "req789",
  "timestamp": "2025-02-08T10:30:05Z",
  "processingTime": 145,
  "result": {
    "decision": "FLAGGED",
    "confidence": 0.92,
    "analysis": {
      "language": "en",
      "toxicity": 0.85,
      "sentiment": -0.7,
      "categories": {
        "PROFANITY": {
          "score": 0.89,
          "verdict": "FLAGGED",
          "violations": [
            {
              "text": "offensive_word",
              "position": {
                "start": 10,
                "end": 15
              },
              "confidence": 0.92,
              "severity": "HIGH"
            }
          ]
        }
      }
    },
    "recommendations": {
      "action": "BLOCK",
      "reason": "HIGH_TOXICITY",
      "suggestedEdits": [
        {
          "original": "offensive_word",
          "suggestion": "[removed]",
          "position": {
            "start": 10,
            "end": 15
          }
        }
      ]
    },
    "metadata": {
      "processedAt": "2025-02-08T10:30:05Z",
      "modelVersion": "v2.1"
    }
  }
}
```

## 2. Batch Text Moderation

### Endpoint: POST /api/v1/moderate/text/batch

### Request Structure

```json
{
  "items": [
    {
      "id": "text1",
      "content": {
        "text": "First text to moderate",
        "language": "en",
        "context": {
          "domain": "social_media",
          "contentType": "comment"
        }
      }
    },
    {
      "id": "text2",
      "content": {
        "text": "Second text to moderate",
        "language": "es",
        "context": {
          "domain": "social_media",
          "contentType": "comment"
        }
      }
    }
  ],
  "configuration": {
    "sensitivityLevel": "MEDIUM",
    "categories": ["PROFANITY", "HATE_SPEECH"]
  },
  "metadata": {
    "clientId": "client123",
    "requestId": "batch456",
    "timestamp": "2025-02-08T10:30:00Z"
  }
}
```

### Success Response (200 OK)

```json
{
  "status": "SUCCESS",
  "requestId": "batch456",
  "timestamp": "2025-02-08T10:30:07Z",
  "processingTime": 250,
  "batchResults": {
    "total": 2,
    "processed": 2,
    "flagged": 1,
    "items": [
      {
        "id": "text1",
        "decision": "APPROVED",
        "confidence": 0.95,
        "analysis": {
          "language": "en",
          "toxicity": 0.02,
          "categories": {
            "PROFANITY": {
              "score": 0.01,
              "verdict": "CLEAN"
            }
          }
        }
      },
      {
        "id": "text2",
        "decision": "FLAGGED",
        "confidence": 0.88,
        "analysis": {
          "language": "es",
          "toxicity": 0.75,
          "categories": {
            "PROFANITY": {
              "score": 0.82,
              "verdict": "FLAGGED",
              "violations": [
                {
                  "text": "offensive_word",
                  "position": {
                    "start": 5,
                    "end": 10
                  },
                  "confidence": 0.88,
                  "severity": "MEDIUM"
                }
              ]
            }
          }
        }
      }
    ]
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "status": "ERROR",
  "timestamp": "2025-02-08T10:30:00Z",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "content.text",
        "message": "Text content cannot be empty"
      }
    ]
  }
}
```

### 401 Unauthorized
```json
{
  "status": "ERROR",
  "timestamp": "2025-02-08T10:30:00Z",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired authentication token"
  }
}
```

### 429 Too Many Requests
```json
{
  "status": "ERROR",
  "timestamp": "2025-02-08T10:30:00Z",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "retryAfter": 60,
      "limit": 100,
      "period": "1 minute"
    }
  }
}
```

### 500 Internal Server Error
```json
{
  "status": "ERROR",
  "timestamp": "2025-02-08T10:30:00Z",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred",
    "traceId": "trace123"
  }
}
```