# HotLabel User Profiling Service

This microservice handles user session management, profile creation, and expertise tracking for the HotLabel platform.

## Features

- Anonymous user session management
- User profiling and expertise inference
- Task compatibility assessment
- Expert network opt-in management
- Performance tracking and analytics

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Running the Service

```bash
# Using Docker
docker-compose up -d

# Without Docker
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8001/api/v1/docs
- ReDoc: http://localhost:8001/api/v1/redoc
