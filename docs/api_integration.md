# API Integration Guide

This document explains how the User Profiling Service integrates with other HotLabel services and external systems.

## Integration with HotLabel Services

The User Profiling Service integrates with other HotLabel microservices to form a complete platform.

### Task Management Service

The User Profiling Service communicates with the Task Management Service to:

- **Receive task information** for compatibility scoring
- **Send user profiles** for task distribution
- **Update task history** for user session records

#### Key Integration Points:

- `GET /api/v1/tasks/available`: Retrieves available tasks for user matching
- `POST /api/v1/tasks/{task_id}/assignments`: Creates a task assignment for a user
- `PATCH /api/v1/tasks/{task_id}/assignments/{assignment_id}`: Updates task assignment status

#### Sample Request:

```http
GET /api/v1/tasks/available?language=en&expertise=technology&level=2 HTTP/1.1
Host: tasks.hotlabel.io
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

#### Sample Response:

```json
{
  "tasks": [
    {
      "task_id": "task_123abc",
      "type": "vqa",
      "language": "en",
      "complexity_level": 2,
      "expertise_area": "technology",
      "estimated_time_ms": 15000
    },
    ...
  ],
  "total": 5,
  "limit": 10,
  "offset": 0
}
```

### Quality Assurance Service

The User Profiling Service integrates with the QA Service to:

- **Receive quality metrics** for user performance evaluation
- **Update user expertise levels** based on quality scores
- **Validate user progression** through expertise levels

#### Key Integration Points:

- `GET /api/v1/quality/metrics/{session_id}`: Retrieve quality metrics for a user session
- `GET /api/v1/quality/metrics/{profile_id}`: Retrieve quality metrics for a user profile
- `POST /api/v1/quality/validate`: Validate a user's expertise level

#### Sample Request:

```http
GET /api/v1/quality/metrics/prof_a1b2c3d4 HTTP/1.1
Host: qa.hotlabel.io
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

#### Sample Response:

```json
{
  "profile_id": "prof_a1b2c3d4",
  "metrics": {
    "total_labels": 156,
    "average_quality_score": 0.92,
    "golden_set_accuracy": 0.94,
    "consensus_rate": 0.89,
    "suspicious_activity_percentage": 0.01,
    "average_time_per_task_ms": 12500
  },
  "expertise_areas": {
    "technology": {
      "total_labels": 98,
      "average_quality_score": 0.95
    },
    "science": {
      "total_labels": 58,
      "average_quality_score": 0.87
    }
  }
}
```

### Publisher Service

The User Profiling Service communicates with the Publisher Service to:

- **Validate publisher IDs** in user sessions
- **Apply publisher-specific profiling rules**
- **Support publisher customizations** of user experience

#### Key Integration Points:

- `GET /api/v1/publishers/{publisher_id}`: Retrieve publisher information
- `GET /api/v1/publishers/{publisher_id}/settings`: Retrieve publisher settings
- `POST /api/v1/publishers/{publisher_id}/events`: Send events/metrics to publisher

## External Integrations

### Client SDK Integration

The HotLabel JavaScript SDK integrates with the User Profiling Service to:

- **Create and manage user sessions**
- **Collect browser signals** for profiling
- **Handle user consent** and privacy preferences

#### JavaScript SDK Example:

```javascript
// Initialize the HotLabel SDK
HotLabel.init({
  publisherId: 'pub_123abc',
  privacySettings: {
    requireConsent: true,
    anonymizeData: true
  }
});

// Create a user session
const session = await HotLabel.createSession();

// Get a compatible task
const task = await HotLabel.getTask();

// Submit a completed task
const result = await HotLabel.submitTask({
  taskId: task.id,
  response: 'user_response',
  timeSpentMs: 5000
});
```

### API Authentication

All service-to-service communication uses API key authentication:

```http
GET /api/v1/resource HTTP/1.1
Host: api.hotlabel.io
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

### Webhooks

The User Profiling Service can push events to external systems via webhooks:

- **Session creation** and expiration events
- **Profile updates** and expertise changes
- **Significant milestone** achievements

#### Webhook Payload Example:

```json
{
  "event_type": "expertise_level_up",
  "timestamp": "2025-04-20T16:45:30Z",
  "data": {
    "profile_id": "prof_a1b2c3d4",
    "session_id": "sess_e5f6g7h8",
    "previous_level": 1,
    "new_level": 2,
    "expertise_area": "technology"
  }
}
```

## API Rate Limits

To ensure system stability, API rate limits are in place:

| Endpoint | Rate Limit |
|----------|------------|
| Session creation | 60 requests per minute per publisher |
| Session updates | 120 requests per minute per publisher |
| Profile operations | 30 requests per minute per publisher |
| Task compatibility checks | 60 requests per minute per publisher |
| Statistics | 20 requests per minute per publisher |

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1618745416
```

## Error Handling

All services use a standardized error response format:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "The publisher_id parameter is required",
    "details": {
      "field": "publisher_id",
      "reason": "missing_required_field"
    },
    "request_id": "req_7890123456"
  }
}
```

## Versioning

The API uses URI versioning (e.g., `/v1/`). When a new version is introduced, the previous version will be supported for at least 12 months.
