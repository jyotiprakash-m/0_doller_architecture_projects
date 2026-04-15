from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./geo_sentinel.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    industry = Column(String)
    location = Column(String)
    website = Column(String, nullable=True)


class SEOAuditReport(Base):
    __tablename__ = "seo_audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Overall score
    overall_score = Column(Integer)

    # Sub-scores for the radar chart
    google_presence_score = Column(Integer, default=50)
    content_score = Column(Integer, default=50)
    social_score = Column(Integer, default=50)

    # Text Analysis Fields
    competitor_analysis = Column(Text)
    social_analysis = Column(Text)
    actionable_steps = Column(Text)
    raw_data = Column(Text)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Now that handles are stable, we just create if not exists
    Base.metadata.create_all(bind=engine)
