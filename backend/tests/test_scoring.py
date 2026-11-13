from app.scoring import skill_metrics
from app.models import User, Skill
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_skill_without_signals_reports_insufficient_data():
    engine = create_engine("sqlite://", connect_args={"check_same_thread":False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    user = User(name="Test",email="test@example.com",password_hash="x")
    db.add(user); db.commit(); db.refresh(user)
    skill = Skill(user_id=user.id,name="Rust",category="Programming")
    db.add(skill); db.commit(); db.refresh(skill)
    result = skill_metrics(db,skill)
    assert result["health"] is None
    assert result["status"] == "Insufficient Data"
    db.close()
