"""
Lookup Table Schemas (Pydantic)

진료과/주치의 관리용 스키마
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Department Schemas =====

class DepartmentBase(BaseModel):
    """Base department schema."""
    name: str = Field(..., min_length=1, max_length=100, description="진료과 이름")
    code: Optional[str] = Field(None, max_length=20, description="진료과 코드 (선택)")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    """Schema for department list response with physician count."""
    id: int
    name: str
    code: Optional[str]
    is_active: bool
    physician_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== Physician Schemas =====

class PhysicianBase(BaseModel):
    """Base physician schema."""
    name: str = Field(..., min_length=1, max_length=100, description="주치의 이름")
    department_id: int = Field(..., description="소속 진료과 ID")
    license_number: Optional[str] = Field(None, max_length=50, description="의사면허번호")
    specialty: Optional[str] = Field(None, max_length=100, description="전문 분야")


class PhysicianCreate(PhysicianBase):
    """Schema for creating a physician."""
    pass


class PhysicianUpdate(BaseModel):
    """Schema for updating a physician."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    department_id: Optional[int] = None
    license_number: Optional[str] = Field(None, max_length=50)
    specialty: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class PhysicianResponse(PhysicianBase):
    """Schema for physician response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PhysicianWithDepartmentResponse(PhysicianResponse):
    """Schema for physician response with department name."""
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
