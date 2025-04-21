import pytest
from app.services.task_compatibility_service import TaskCompatibilityService

@pytest.fixture
def service(mocker):
    session_repo = mocker.Mock()
    profile_repo = mocker.Mock()
    statistics_repo = mocker.Mock()
    expertise_repo = mocker.Mock()
    return TaskCompatibilityService(session_repo, profile_repo, statistics_repo, expertise_repo)

@pytest.mark.asyncio
async def test_get_compatible_tasks(service, mocker):
    # Mock DB and user data
    mock_db = mocker.Mock()
    mocker.patch.object(service, "_get_user_data", return_value={"id": "user1", "language": "en"})
    mocker.patch.object(service, "_calculate_language_compatibility", return_value=1.0)
    mocker.patch.object(service, "_calculate_complexity_compatibility", return_value=0.8)
    mocker.patch.object(service, "_calculate_category_compatibility", return_value=0.9)

    result = await service.get_compatible_tasks(mock_db, "user1")
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_calculate_task_compatibility(service, mocker):
    mock_db = mocker.Mock()
    mocker.patch.object(service, "_get_user_data", return_value={"id": "user1", "language": "en"})
    mocker.patch.object(service, "_calculate_language_compatibility", return_value=1.0)
    mocker.patch.object(service, "_calculate_complexity_compatibility", return_value=0.8)
    mocker.patch.object(service, "_calculate_category_compatibility", return_value=0.9)

    result = await service.calculate_task_compatibility(mock_db, "user1", "task1")
    assert isinstance(result, dict)
    assert "compatibility_score" in result

@pytest.mark.asyncio
async def test_recommend_next_task_level(service, mocker):
    mock_db = mocker.Mock()
    mocker.patch.object(service, "_get_user_data", return_value={"id": "user1", "language": "en"})

    result = await service.recommend_next_task_level(mock_db, "user1")
    assert isinstance(result, dict)
    assert "recommended_level" in result
