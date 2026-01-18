"""
Role-Based Access Control (RBAC)

Roles:
- REPORTER: Basic incident reporting
- QPS_STAFF: Department-level access + L1 approval
- VICE_CHAIR: All access + L2 approval
- DIRECTOR: All access + L3 approval + archive
- ADMIN: System config only (no data access)
- MASTER: All permissions (superuser)
"""

from enum import Enum
from typing import Set

from app.models.user import Role


class Permission(str, Enum):
    """System permissions."""

    # Incident permissions
    CREATE_INCIDENT = "create_incident"
    VIEW_INCIDENT = "view_incident"
    EDIT_INCIDENT = "edit_incident"
    DELETE_INCIDENT = "delete_incident"
    EXPORT_INCIDENT = "export_incident"

    # Attachment permissions
    UPLOAD_ATTACHMENT = "upload_attachment"
    VIEW_ATTACHMENT = "view_attachment"
    DELETE_ATTACHMENT = "delete_attachment"

    # Approval permissions
    APPROVE_L1 = "approve_l1"
    APPROVE_L2 = "approve_l2"
    APPROVE_L3 = "approve_l3"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    SYSTEM_CONFIG = "system_config"

    # Indicator permissions
    VIEW_INDICATORS = "view_indicators"
    MANAGE_INDICATORS = "manage_indicators"
    INPUT_INDICATOR_VALUES = "input_indicator_values"
    VERIFY_INDICATOR_VALUES = "verify_indicator_values"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.REPORTER: {
        Permission.CREATE_INCIDENT,
        Permission.VIEW_INCIDENT,  # Own only (row-level)
        Permission.EDIT_INCIDENT,  # Own draft only (row-level)
        Permission.UPLOAD_ATTACHMENT,  # Own incidents only
        Permission.VIEW_ATTACHMENT,  # Own incidents only
        Permission.VIEW_INDICATORS,  # View only
    },
    Role.QPS_STAFF: {
        Permission.CREATE_INCIDENT,
        Permission.VIEW_INCIDENT,  # Department (row-level)
        Permission.EDIT_INCIDENT,  # Department (row-level)
        Permission.EXPORT_INCIDENT,  # Department only
        Permission.UPLOAD_ATTACHMENT,
        Permission.VIEW_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,  # Own uploads
        Permission.APPROVE_L1,
        Permission.VIEW_INDICATORS,
        Permission.INPUT_INDICATOR_VALUES,
    },
    Role.VICE_CHAIR: {
        Permission.CREATE_INCIDENT,
        Permission.VIEW_INCIDENT,  # All
        Permission.EDIT_INCIDENT,  # All
        Permission.EXPORT_INCIDENT,  # All
        Permission.UPLOAD_ATTACHMENT,
        Permission.VIEW_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,
        Permission.APPROVE_L1,
        Permission.APPROVE_L2,
        Permission.VIEW_INDICATORS,
        Permission.INPUT_INDICATOR_VALUES,
        Permission.VERIFY_INDICATOR_VALUES,
    },
    Role.DIRECTOR: {
        Permission.CREATE_INCIDENT,
        Permission.VIEW_INCIDENT,  # All
        Permission.EDIT_INCIDENT,  # All
        Permission.DELETE_INCIDENT,  # Archive only
        Permission.EXPORT_INCIDENT,  # All
        Permission.UPLOAD_ATTACHMENT,
        Permission.VIEW_ATTACHMENT,
        Permission.DELETE_ATTACHMENT,
        Permission.APPROVE_L1,
        Permission.APPROVE_L2,
        Permission.APPROVE_L3,
        Permission.VIEW_INDICATORS,
        Permission.MANAGE_INDICATORS,
        Permission.INPUT_INDICATOR_VALUES,
        Permission.VERIFY_INDICATOR_VALUES,
    },
    Role.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.SYSTEM_CONFIG,
        # Note: ADMIN has NO data access permissions
    },
    Role.MASTER: set(Permission),  # All permissions (superuser)
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
