"""
Indicator Schemas (Pydantic)

Schemas for:
- IndicatorConfig: Indicator configuration/definition
- IndicatorValue: Indicator measurement values
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.indicator import (
    IndicatorCategory,
    IndicatorStatus,
    ThresholdDirection,
    PeriodType,
    ChartType,
)


# ===== IndicatorConfig Schemas =====

class IndicatorConfigBase(BaseModel):
    """Base indicator configuration schema."""

    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Indicator code (e.g., PSR-001) - auto-generated if not provided")
    name: str = Field(..., min_length=1, max_length=200, description="Indicator name")
    category: IndicatorCategory
    description: Optional[str] = Field(None, max_length=1000)
    unit: str = Field(default="건", min_length=1, max_length=50, description="Unit of measure")

    # Calculation method
    calculation_formula: Optional[str] = Field(None, max_length=500, description="Formula description")
    numerator_name: Optional[str] = Field(None, max_length=500, description="Numerator description")
    denominator_name: Optional[str] = Field(None, max_length=500, description="Denominator description")

    # Target and thresholds
    target_value: Optional[float] = Field(None, description="Target value")
    warning_threshold: Optional[float] = Field(None, description="Warning threshold")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold")
    threshold_direction: Optional[ThresholdDirection] = None

    # Display settings
    period_type: PeriodType = Field(default=PeriodType.MONTHLY)
    chart_type: ChartType = Field(default=ChartType.LINE)
    is_key_indicator: bool = Field(default=False, description="Mark as key indicator")
    display_order: int = Field(default=0, ge=0)

    # Data settings
    data_source: Optional[str] = Field(None, max_length=200)
    auto_calculate: bool = Field(default=False, description="Auto-calculate from related data")

    status: IndicatorStatus = Field(default=IndicatorStatus.ACTIVE)

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate code format (e.g., PSR-001, PU-001) if provided."""
        import re
        if v is None or v == "":
            return None  # Allow None for auto-generation
        if not re.match(r"^[A-Z]{2,5}-\d{3}$", v.upper()):
            raise ValueError("Code must be in format like PSR-001, PU-001")
        return v.upper()


class IndicatorConfigCreate(IndicatorConfigBase):
    """Schema for creating an indicator configuration."""
    pass


class IndicatorConfigUpdate(BaseModel):
    """Schema for updating an indicator configuration."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[IndicatorCategory] = None
    description: Optional[str] = Field(None, max_length=1000)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)

    calculation_formula: Optional[str] = Field(None, max_length=500)
    numerator_name: Optional[str] = Field(None, max_length=500)
    denominator_name: Optional[str] = Field(None, max_length=500)

    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    threshold_direction: Optional[ThresholdDirection] = None

    period_type: Optional[PeriodType] = None
    chart_type: Optional[ChartType] = None
    is_key_indicator: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)

    data_source: Optional[str] = Field(None, max_length=200)
    auto_calculate: Optional[bool] = None

    status: Optional[IndicatorStatus] = None

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^[A-Z]{2,5}-\d{3}$", v.upper()):
            raise ValueError("Code must be in format like PSR-001, PU-001")
        return v.upper()


class IndicatorConfigResponse(BaseModel):
    """Schema for indicator configuration response."""

    id: int
    code: str
    name: str
    category: IndicatorCategory
    description: Optional[str] = None
    unit: str

    calculation_formula: Optional[str] = None
    numerator_name: Optional[str] = None
    denominator_name: Optional[str] = None

    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    threshold_direction: Optional[ThresholdDirection] = None

    period_type: PeriodType
    chart_type: ChartType
    is_key_indicator: bool
    display_order: int

    data_source: Optional[str] = None
    auto_calculate: bool

    status: IndicatorStatus

    # 승인 워크플로우 필드
    approval_requested_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    rejection_reason: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class IndicatorApproveRequest(BaseModel):
    """Schema for approving an indicator."""
    comment: Optional[str] = Field(None, max_length=500)


class IndicatorRejectRequest(BaseModel):
    """Schema for rejecting an indicator."""
    reason: str = Field(..., min_length=1, max_length=500, description="반려 사유 (필수)")


class IndicatorConfigListResponse(BaseModel):
    """Schema for indicator configuration list response."""

    items: List[IndicatorConfigResponse]
    total: int
    skip: int
    limit: int


# ===== IndicatorValue Schemas =====

class IndicatorValueCreate(BaseModel):
    """Schema for creating an indicator value."""

    period_start: datetime
    period_end: datetime
    value: float
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=500)


class IndicatorValueUpdate(BaseModel):
    """Schema for updating an indicator value."""

    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    value: Optional[float] = None
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=500)


class IndicatorValueResponse(BaseModel):
    """Schema for indicator value response."""

    id: int
    indicator_id: int
    period_start: datetime
    period_end: datetime
    value: float
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    notes: Optional[str] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class IndicatorValueListResponse(BaseModel):
    """Schema for indicator value list response."""

    items: List[IndicatorValueResponse]
    total: int
    skip: int
    limit: int


class IndicatorValueVerifyRequest(BaseModel):
    """Schema for verifying an indicator value."""

    comment: Optional[str] = Field(None, max_length=500)
