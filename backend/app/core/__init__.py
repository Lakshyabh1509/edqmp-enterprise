"""
EDQMP Core Module
"""

from app.core.config import settings, get_settings
from app.core.database import (
    DatabaseManager,
    get_supabase,
    get_db,
    Base
)
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    verify_supabase_token,
    require_admin,
    require_moderator
)

__all__ = [
    "settings",
    "get_settings",
    "DatabaseManager",
    "get_supabase",
    "get_db",
    "Base",
    "get_current_user",
    "get_current_user_optional",
    "verify_supabase_token",
    "require_admin",
    "require_moderator"
]
