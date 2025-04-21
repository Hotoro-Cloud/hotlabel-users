# HotLabel User Profiling Service

This microservice handles user session management, profile creation, and expertise tracking for the HotLabel platform. It implements a privacy-first approach to user profiling for the crowdsourced data labeling system.

## Features

- **Anonymous User Session Management**: Track user activity without storing PII
- **User Profiling**: Infer expertise, interests, and skills based on user behavior
- **Expertise Classification**: Categorize users by domain knowledge and skill level
- **Task Compatibility Engine**: Match users with appropriate labeling tasks
- **Expert Network**: Allow users to opt-in for enhanced profiles
- **Performance Analytics**: Track quality metrics and engagement statistics

## Architecture

The service follows a clean architecture pattern with clear separation of concerns:

- **API Layer**: REST endpoints for service interaction
- **Service Layer**: Business logic and core functionality
- **Repository Layer**: Data access and persistence
- **Models**: Database schemas and entity definitions

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create a new anonymous session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `PATCH /api/v1/sessions/{session_id}` - Update session data

### Profiles
- `POST /api/v1/profiles` - Create user profile (opt-in to expert network)
- `GET /api/v1/profiles/{profile_id}` - Get user profile
- `PUT /api/v1/profiles/{profile_id}` - Update user profile
- `DELETE /api/v1/profiles/{profile_id}` - Delete user profile

### Task Compatibility
- `GET /api/v1/users/{session_id}/task-compatibility` - Get task compatibility scores
- `POST /api/v1/users/{session_id}/task-completions` - Record task completion

### Statistics
- `GET /api/v1/statistics/users/{user_id}` - Get user performance statistics
- `GET /api/v1/statistics/publishers/{publisher_id}` - Get publisher statistics

### Expertise Areas
- `GET /api/v1/expertise` - List all expertise areas
- `GET /api/v1/expertise/{area_id}` - Get expertise area details

## Data Privacy

- All user data is anonymized by default
- Personal information is never stored without explicit consent
- Session data is automatically purged after a configurable period
- Profile creation is opt-in and requires explicit consent

## Installation and Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Environment Variables

Copy the `.env.example` file to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running with Docker

```bash
docker-compose up -d
```

### Running Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8001
```

## API Documentation

Once the service is running, you can access the API documentation at:

- Swagger UI: http://localhost:8001/api/v1/docs
- ReDoc: http://localhost:8001/api/v1/docs/redoc

## Integration with Other Services

This service integrates with:

- **Task Management Service**: For task compatibility and assignment
- **Quality Assurance Service**: For performance metrics and validation
- **Publisher Service**: For publisher-specific customization

## Development

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Tests

```bash
pytest
```

#### Test Coverage

The following test files are included to ensure robust coverage of the application's API and business logic:

- **tests/test_api_integration.py**: End-to-end integration flows for session creation, profile linking, task completion, and expertise area management.
- **tests/test_profile_routes.py**: CRUD and list tests for user profile API endpoints.
- **tests/test_statistics_routes.py**: Tests for user and session statistics API endpoints.
- **tests/test_task_compatibility_service.py**: Unit tests for TaskCompatibilityService methods, using mocks for dependencies.
- **tests/test_user_routes.py**: Tests for user API endpoints including search, task compatibility, user matching, and language detection.
- **tests/test_profiler_service.py**: Unit tests for ProfilerService logic, including browser signal analysis, expertise inference, and language proficiency.
- **tests/test_session_routes.py**: CRUD, update, and task completion tests for session API endpoints.

Test fixtures for user sessions, profiles, and expertise areas are defined in `tests/conftest.py` for consistent and isolated test data.

To run all tests:
```bash
pytest
```
