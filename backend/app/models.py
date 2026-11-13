from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship
from .database import Base

evidence_skills = Table(
    "evidence_skills", Base.metadata,
    Column("evidence_id", ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(80), default="Technical")
    self_rating = Column(Integer, default=3)
    target_rating = Column(Integer, default=4)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="skills")
    activities = relationship("Activity", back_populates="skill", cascade="all, delete-orphan")
    evidence = relationship("Evidence", secondary=evidence_skills, back_populates="skills")
    attempts = relationship("AssessmentAttempt", back_populates="skill", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    description = Column(Text, default="")
    activity_type = Column(String(40), default="Practice")
    duration_minutes = Column(Integer, default=30)
    difficulty = Column(String(30), default="Intermediate")
    score = Column(Float, nullable=True)
    activity_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="activities")
    skill = relationship("Skill", back_populates="activities")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    evidence_type = Column(String(40), default="Project")
    description = Column(Text, default="")
    url = Column(String(1000), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="evidence")
    skills = relationship("Skill", secondary=evidence_skills, back_populates="evidence")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id = Column(Integer, primary_key=True)
    skill_name = Column(String(100), index=True, nullable=False)
    difficulty = Column(String(30), default="Intermediate")
    question = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    correct_index = Column(Integer, nullable=False)
    explanation = Column(Text, default="")

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="attempts")
    skill = relationship("Skill", back_populates="attempts")
