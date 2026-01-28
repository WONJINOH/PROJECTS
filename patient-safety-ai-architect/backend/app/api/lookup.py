"""
Lookup API (진료과/주치의 관리)

Admin 권한 필요 CRUD API
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lookup import Department, Physician
from app.models.user import User, Role
from app.schemas.lookup import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
    PhysicianCreate,
    PhysicianUpdate,
    PhysicianResponse,
    PhysicianWithDepartmentResponse,
)
from app.security.dependencies import get_current_user, require_role

router = APIRouter()


# ===== Department APIs =====

@router.get("/departments", response_model=list[DepartmentListResponse])
async def list_departments(
    active_only: bool = True,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    진료과 목록 조회

    - 모든 인증된 사용자가 조회 가능 (폼 드롭다운용)
    - active_only=True: 활성 진료과만 조회 (기본값)
    """
    # Subquery to count active physicians per department
    physician_count_subq = (
        select(
            Physician.department_id,
            func.count(Physician.id).label("physician_count")
        )
        .where(Physician.is_active == True)
        .group_by(Physician.department_id)
        .subquery()
    )

    query = (
        select(
            Department.id,
            Department.name,
            Department.code,
            Department.is_active,
            Department.created_at,
            func.coalesce(physician_count_subq.c.physician_count, 0).label("physician_count"),
        )
        .outerjoin(physician_count_subq, Department.id == physician_count_subq.c.department_id)
    )

    if active_only:
        query = query.where(Department.is_active == True)

    query = query.order_by(Department.name)

    result = await db.execute(query)
    rows = result.all()

    return [
        DepartmentListResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            is_active=r.is_active,
            physician_count=r.physician_count,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """진료과 상세 조회"""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    진료과 생성 (Admin 권한 필요)
    """
    # Check for duplicate name
    result = await db.execute(
        select(Department).where(Department.name == data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Department with this name already exists")

    # Check for duplicate code if provided
    if data.code:
        result = await db.execute(
            select(Department).where(Department.code == data.code)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Department with this code already exists")

    department = Department(**data.model_dump())
    db.add(department)
    await db.commit()
    await db.refresh(department)

    return department


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    진료과 수정 (Admin 권한 필요)
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for duplicate name if being updated
    if "name" in update_data and update_data["name"] != department.name:
        result = await db.execute(
            select(Department).where(
                Department.name == update_data["name"],
                Department.id != department_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Department with this name already exists")

    # Check for duplicate code if being updated
    if "code" in update_data and update_data["code"] and update_data["code"] != department.code:
        result = await db.execute(
            select(Department).where(
                Department.code == update_data["code"],
                Department.id != department_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Department with this code already exists")

    for key, value in update_data.items():
        setattr(department, key, value)

    await db.commit()
    await db.refresh(department)

    return department


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    진료과 삭제 (Admin 권한 필요)

    - 연결된 주치의가 있으면 삭제 불가
    - 대신 is_active=False로 비활성화 권장
    """
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check for linked physicians
    result = await db.execute(
        select(func.count(Physician.id)).where(Physician.department_id == department_id)
    )
    physician_count = result.scalar()
    if physician_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {physician_count} linked physicians. Deactivate instead.",
        )

    await db.delete(department)
    await db.commit()


# ===== Physician APIs =====

@router.get("/physicians", response_model=list[PhysicianWithDepartmentResponse])
async def list_physicians(
    department_id: Optional[int] = None,
    active_only: bool = True,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    주치의 목록 조회

    - 모든 인증된 사용자가 조회 가능 (폼 드롭다운용)
    - department_id: 특정 진료과의 주치의만 조회
    - active_only=True: 활성 주치의만 조회 (기본값)
    """
    query = (
        select(
            Physician.id,
            Physician.name,
            Physician.department_id,
            Department.name.label("department_name"),
            Physician.license_number,
            Physician.specialty,
            Physician.is_active,
            Physician.created_at,
            Physician.updated_at,
        )
        .join(Department, Physician.department_id == Department.id)
    )

    if department_id:
        query = query.where(Physician.department_id == department_id)

    if active_only:
        query = query.where(Physician.is_active == True)

    query = query.order_by(Physician.name)

    result = await db.execute(query)
    rows = result.all()

    return [
        PhysicianWithDepartmentResponse(
            id=r.id,
            name=r.name,
            department_id=r.department_id,
            department_name=r.department_name,
            license_number=r.license_number,
            specialty=r.specialty,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/physicians/{physician_id}", response_model=PhysicianWithDepartmentResponse)
async def get_physician(
    physician_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """주치의 상세 조회"""
    result = await db.execute(
        select(
            Physician.id,
            Physician.name,
            Physician.department_id,
            Department.name.label("department_name"),
            Physician.license_number,
            Physician.specialty,
            Physician.is_active,
            Physician.created_at,
            Physician.updated_at,
        )
        .join(Department, Physician.department_id == Department.id)
        .where(Physician.id == physician_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Physician not found")

    return PhysicianWithDepartmentResponse(
        id=row.id,
        name=row.name,
        department_id=row.department_id,
        department_name=row.department_name,
        license_number=row.license_number,
        specialty=row.specialty,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/physicians", response_model=PhysicianResponse, status_code=status.HTTP_201_CREATED)
async def create_physician(
    data: PhysicianCreate,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    주치의 생성 (Admin 권한 필요)
    """
    # Check department exists
    result = await db.execute(
        select(Department).where(Department.id == data.department_id)
    )
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    if not department.is_active:
        raise HTTPException(status_code=400, detail="Cannot add physician to inactive department")

    physician = Physician(**data.model_dump())
    db.add(physician)
    await db.commit()
    await db.refresh(physician)

    return physician


@router.put("/physicians/{physician_id}", response_model=PhysicianResponse)
async def update_physician(
    physician_id: int,
    data: PhysicianUpdate,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    주치의 수정 (Admin 권한 필요)
    """
    result = await db.execute(
        select(Physician).where(Physician.id == physician_id)
    )
    physician = result.scalar_one_or_none()
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check department if being updated
    if "department_id" in update_data:
        result = await db.execute(
            select(Department).where(Department.id == update_data["department_id"])
        )
        department = result.scalar_one_or_none()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found")
        if not department.is_active:
            raise HTTPException(status_code=400, detail="Cannot move physician to inactive department")

    for key, value in update_data.items():
        setattr(physician, key, value)

    await db.commit()
    await db.refresh(physician)

    return physician


@router.delete("/physicians/{physician_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_physician(
    physician_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))] = None,
):
    """
    주치의 삭제 (Admin 권한 필요)

    Note: 실제 삭제 대신 is_active=False로 비활성화 권장
    """
    result = await db.execute(
        select(Physician).where(Physician.id == physician_id)
    )
    physician = result.scalar_one_or_none()
    if not physician:
        raise HTTPException(status_code=404, detail="Physician not found")

    await db.delete(physician)
    await db.commit()
