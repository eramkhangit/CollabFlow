# app/models/__init__.py
# Yahan sab models ek saath import karo

from app.models.auth import UserModel, Permissions
from app.models.project import Project
from app.models.ticket import Ticket

__all__ = ['UserModel', 'Project', 'Ticket', 'Permissions']