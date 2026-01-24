"""
Indicator Management API

Endpoints for managing indicator configurations and values.
Implements RBAC for indicator access control.
"""

from typing import Annotated, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.indicator import (
    IndicatorConfig,
    IndicatorValue,
    IndicatorCategory,
    IndicatorStatus,
)
from app.schemas.indicator import (
    IndicatorConfigCreate,
    IndicatorConfigUpdate,
    IndicatorConfigResponse,
    IndicatorConfigListResponse,
    IndicatorValueCreate,
    IndicatorValueUpdate,
    IndicatorValueResponse,
    IndicatorValueListResponse,
    IndicatorValueVerifyRequest,
)
from app.security.dependencies import get_current_user, require_permission
from app.security.rbac import Permission
from app.models.user import User

router = APIRouter()


# ===== Indicator Config Endpoints =====

@router.get(
    "/",
    response_model=IndicatorConfigListResponse,
    summary="List indicator configurations",
)
async def list_indicators(
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_INDICATORS))],
    db: AsyncSession = Depends(get_db),
    category: Optional[IndicatorCategory] = Query(None, description="Filter by category"),
    status_filter: Optional[IndicatorStatus] = Query(None, alias="status", description="Filter by status"),
    is_key: Optional[bool] = Query(None, description="Filter key indicators only"),
    search: Optional[str] = Query(None, description="Search by code or name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> IndicatorConfigListResponse:
    """
    List indicator configurations with filtering.

    Filters:
    - category: Filter by indicator category
    - status: Filter by status (active, inactive, planned)
    - is_key: Filter key indicators only
    - search: Search by code or name
    """
    # Build query
    query = select(IndicatorConfig)

    # Apply filters
    if category:
        query = query.where(IndicatorConfig.category == category)
    if status_filter:
        query = query.where(IndicatorConfig.status == status_filter)
    if is_key is not None:
        query = query.where(IndicatorConfig.is_key_indicator == is_key)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                IndicatorConfig.code.ilike(search_pattern),
                IndicatorConfig.name.ilike(search_pattern),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(
        IndicatorConfig.category,
        IndicatorConfig.display_order,
        IndicatorConfig.code,
    )
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    indicators = result.scalars().all()

    return IndicatorConfigListResponse(
        items=[IndicatorConfigResponse.model_validate(ind) for ind in indicators],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=IndicatorConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create indicator configuration",
)
async def create_indicator(
    indicator: IndicatorConfigCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.MANAGE_INDICATORS))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorConfigResponse:
    """
    Create a new indicator configuration.

    Required fields:
    - code: Unique indicator code (e.g., PSR-001)
    - name: Indicator name
    - category: Indicator category
    - unit: Unit of measure
    """
    # Check code uniqueness
    existing = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.code == indicator.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Indicator with code '{indicator.code}' already exists",
        )

    # Create indicator
    db_indicator = IndicatorConfig(
        code=indicator.code,
        name=indicator.name,
        category=indicator.category,
        description=indicator.description,
        unit=indicator.unit,
        calculation_formula=indicator.calculation_formula,
        numerator_name=indicator.numerator_name,
        denominator_name=indicator.denominator_name,
        target_value=indicator.target_value,
        warning_threshold=indicator.warning_threshold,
        critical_threshold=indicator.critical_threshold,
        threshold_direction=indicator.threshold_direction,
        period_type=indicator.period_type,
        chart_type=indicator.chart_type,
        is_key_indicator=indicator.is_key_indicator,
        display_order=indicator.display_order,
        data_source=indicator.data_source,
        auto_calculate=indicator.auto_calculate,
        status=indicator.status,
        created_by_id=current_user.id,
    )

    db.add(db_indicator)
    await db.flush()
    await db.refresh(db_indicator)

    return IndicatorConfigResponse.model_validate(db_indicator)


@router.get(
    "/{indicator_id}",
    response_model=IndicatorConfigResponse,
    summary="Get indicator configuration",
)
async def get_indicator(
    indicator_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_INDICATORS))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorConfigResponse:
    """Get details of a specific indicator configuration."""
    result = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found",
        )

    return IndicatorConfigResponse.model_validate(indicator)


@router.put(
    "/{indicator_id}",
    response_model=IndicatorConfigResponse,
    summary="Update indicator configuration",
)
async def update_indicator(
    indicator_id: int,
    indicator_update: IndicatorConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.MANAGE_INDICATORS))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorConfigResponse:
    """Update an existing indicator configuration."""
    # Get existing indicator
    result = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found",
        )

    # Check code uniqueness if changed
    if indicator_update.code and indicator_update.code != indicator.code:
        existing = await db.execute(
            select(IndicatorConfig).where(IndicatorConfig.code == indicator_update.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Indicator with code '{indicator_update.code}' already exists",
            )

    # Update fields
    update_data = indicator_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(indicator, field, value)

    await db.flush()
    await db.refresh(indicator)

    return IndicatorConfigResponse.model_validate(indicator)


@router.delete(
    "/{indicator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete indicator configuration (soft delete)",
)
async def delete_indicator(
    indicator_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.MANAGE_INDICATORS))],
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete an indicator configuration.

    Sets status to INACTIVE instead of physical delete.
    """
    result = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found",
        )

    # Soft delete - set status to inactive
    indicator.status = IndicatorStatus.INACTIVE
    await db.flush()


# ===== Indicator Value Endpoints =====

@router.get(
    "/{indicator_id}/values",
    response_model=IndicatorValueListResponse,
    summary="List indicator values",
)
async def list_indicator_values(
    indicator_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_INDICATORS))],
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Filter by period start"),
    end_date: Optional[datetime] = Query(None, description="Filter by period end"),
    verified_only: bool = Query(False, description="Show only verified values"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> IndicatorValueListResponse:
    """
    List values for a specific indicator.

    Filters:
    - start_date, end_date: Filter by period
    - verified_only: Show only verified values
    """
    # Check indicator exists
    indicator_result = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.id == indicator_id)
    )
    if not indicator_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found",
        )

    # Build query
    query = select(IndicatorValue).where(IndicatorValue.indicator_id == indicator_id)

    if start_date:
        query = query.where(IndicatorValue.period_start >= start_date)
    if end_date:
        query = query.where(IndicatorValue.period_end <= end_date)
    if verified_only:
        query = query.where(IndicatorValue.is_verified == True)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(IndicatorValue.period_start.desc())
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    values = result.scalars().all()

    return IndicatorValueListResponse(
        items=[IndicatorValueResponse.model_validate(v) for v in values],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{indicator_id}/values",
    response_model=IndicatorValueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create indicator value",
)
async def create_indicator_value(
    indicator_id: int,
    value_data: IndicatorValueCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.INPUT_INDICATOR_VALUES))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorValueResponse:
    """
    Create a new indicator value entry.

    Required fields:
    - period_start, period_end: Period range
    - value: Measured value
    """
    # Check indicator exists
    indicator_result = await db.execute(
        select(IndicatorConfig).where(IndicatorConfig.id == indicator_id)
    )
    if not indicator_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found",
        )

    # Create value
    db_value = IndicatorValue(
        indicator_id=indicator_id,
        period_start=value_data.period_start,
        period_end=value_data.period_end,
        value=value_data.value,
        numerator=value_data.numerator,
        denominator=value_data.denominator,
        notes=value_data.notes,
        created_by_id=current_user.id,
    )

    db.add(db_value)
    await db.flush()
    await db.refresh(db_value)

    return IndicatorValueResponse.model_validate(db_value)


@router.put(
    "/values/{value_id}",
    response_model=IndicatorValueResponse,
    summary="Update indicator value",
)
async def update_indicator_value(
    value_id: int,
    value_data: IndicatorValueUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.INPUT_INDICATOR_VALUES))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorValueResponse:
    """Update an existing indicator value."""
    result = await db.execute(
        select(IndicatorValue).where(IndicatorValue.id == value_id)
    )
    value = result.scalar_one_or_none()

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator value with id {value_id} not found",
        )

    # Cannot update verified values
    if value.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a verified value",
        )

    # Update fields
    update_data = value_data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(value, field, val)

    await db.flush()
    await db.refresh(value)

    return IndicatorValueResponse.model_validate(value)


@router.post(
    "/values/{value_id}/verify",
    response_model=IndicatorValueResponse,
    summary="Verify indicator value",
)
async def verify_indicator_value(
    value_id: int,
    verify_request: IndicatorValueVerifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VERIFY_INDICATOR_VALUES))],
    db: AsyncSession = Depends(get_db),
) -> IndicatorValueResponse:
    """
    Verify an indicator value.

    Only users with VERIFY_INDICATOR_VALUES permission can verify.
    """
    result = await db.execute(
        select(IndicatorValue).where(IndicatorValue.id == value_id)
    )
    value = result.scalar_one_or_none()

    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator value with id {value_id} not found",
        )

    if value.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Value is already verified",
        )

    # Verify
    value.is_verified = True
    value.verified_by_id = current_user.id
    value.verified_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(value)

    return IndicatorValueResponse.model_validate(value)
