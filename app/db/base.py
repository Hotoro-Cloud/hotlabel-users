# Import all models here for Alembic to detect them
from app.db.session import Base

# Import models
from app.models.user_session import UserSession
from app.models.user_profile import UserProfile, profile_expertise_table
from app.models.user_statistics import UserStatistics
from app.models.expertise_area import ExpertiseArea
