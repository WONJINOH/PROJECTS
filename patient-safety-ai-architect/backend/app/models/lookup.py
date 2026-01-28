"""
Lookup Tables (진료과/주치의 관리)

Admin 관리용 마스터 테이블
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """진료과 테이블"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(20), nullable=True, unique=True)  # 진료과 코드 (선택)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    physicians = relationship("Physician", back_populates="department")

    def __repr__(self) -> str:
        return f"<Department {self.id}: {self.name}>"


class Physician(Base):
    """주치의 테이블"""

    __tablename__ = "physicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    license_number = Column(String(50), nullable=True)  # 의사면허번호 (선택)
    specialty = Column(String(100), nullable=True)  # 전문 분야 (선택)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    department = relationship("Department", back_populates="physicians")

    def __repr__(self) -> str:
        return f"<Physician {self.id}: {self.name}>"
