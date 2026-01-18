"""
Incident Model

Patient safety incident with required fields per CLAUDE.md:
- immediate_action: REQUIRED for all incidents
- reported_at: REQUIRED (datetime)
- reporter_name: Required except for NEAR_MISS grade
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app.database import Base
from app.config import settings


class IncidentCategory(str, enum.Enum):
    """Incident categories."""

    FALL = "fall"                          # 낙상
    MEDICATION = "medication"              # 투약
    PRESSURE_ULCER = "pressure_ulcer"      # 욕창
    INFECTION = "infection"                # 감염
    MEDICAL_DEVICE = "medical_device"      # 의료기기
    SURGERY = "surgery"                    # 수술
    TRANSFUSION = "transfusion"            # 수혈
    OTHER = "other"                        # 기타


class IncidentGrade(str, enum.Enum):
    """Incident severity grades."""

    NEAR_MISS = "near_miss"    # 근접오류 (reporter_name optional)
    NO_HARM = "no_harm"        # 위해없음
    MILD = "mild"              # 일시적 손상 - 경증
    MODERATE = "moderate"      # 일시적 손상 - 중등도
    SEVERE = "severe"          # 영구적 손상
    DEATH = "death"            # 사망


class Incident(Base):
    """Patient safety incident model."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    # === Common Page Required Fields ===
    category = Column(Enum(IncidentCategory), nullable=False, index=True)
    grade = Column(Enum(IncidentGrade), nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # REQUIRED: immediate action taken
    immediate_action = Column(Text, nullable=False)

    # REQUIRED: when report was created
    reported_at = Column(DateTime, nullable=False)

    # Required EXCEPT for NEAR_MISS (validated in schema)
    reporter_name = Column(String(100), nullable=True)

    # === Optional Fields ===
    root_cause = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)

    # === Sensitive Patient Info (Encrypted) ===
    # Note: In production, use proper key management
    patient_info = Column(
        EncryptedType(Text, settings.DB_ENCRYPTION_KEY, AesEngine, "pkcs5"),
        nullable=True,
    )

    # === Metadata ===
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String(100), nullable=True)
    status = Column(String(50), default="draft", index=True)  # draft, submitted, approved, closed
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reporter = relationship("User", back_populates="incidents")
    attachments = relationship("Attachment", back_populates="incident")
    approvals = relationship("Approval", back_populates="incident")

    def __repr__(self) -> str:
        return f"<Incident {self.id} ({self.category.value}, {self.grade.value})>"
