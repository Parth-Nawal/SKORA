from datetime import datetime, timezone
from math import exp
from sqlalchemy.orm import Session
from .models import Skill, Activity, Evidence, AssessmentAttempt

def skill_metrics(db: Session, skill: Skill) -> dict:
    attempts = db.query(AssessmentAttempt).filter_by(user_id=skill.user_id, skill_id=skill.id).order_by(AssessmentAttempt.completed_at.desc()).all()
    activities = db.query(Activity).filter_by(user_id=skill.user_id, skill_id=skill.id).order_by(Activity.activity_date.desc()).all()
    evidence_count = len([e for e in skill.evidence if e.user_id == skill.user_id])

    if not attempts and not activities and evidence_count == 0:
        return {"health": None, "status": "Insufficient Data", "assessment": None, "recency": None, "consistency": None, "evidence": 0, "last_practiced": None, "confidence": "Low"}

    assessment = sum(a.percentage for a in attempts[:5]) / min(len(attempts), 5) if attempts else None
    now = datetime.now(timezone.utc)
    last = activities[0].activity_date if activities else None
    if last and last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    days = max(0, (now - last).total_seconds() / 86400) if last else None
    recency = 100 * exp(-days / 30) if days is not None else None
    recent_30 = [a for a in activities if ((now - (a.activity_date.replace(tzinfo=timezone.utc) if a.activity_date.tzinfo is None else a.activity_date)).days <= 30)]
    consistency = min(100, len(recent_30) * 20) if activities else None
    evidence_score = min(100, evidence_count * 35) if evidence_count else 0

    components = []
    if assessment is not None: components.append((assessment, 0.40))
    if recency is not None: components.append((recency, 0.25))
    if consistency is not None: components.append((consistency, 0.20))
    if evidence_count: components.append((evidence_score, 0.15))
    total_weight = sum(w for _, w in components)
    health = round(sum(v*w for v, w in components) / total_weight, 1) if total_weight else None
    status = "Insufficient Data" if health is None else "Strong" if health >= 80 else "Stable" if health >= 65 else "Needs Practice" if health >= 45 else "At Risk"
    confidence = "High" if attempts and evidence_count and activities else "Medium" if len(components) >= 2 else "Low"
    return {"health": health, "status": status, "assessment": round(assessment,1) if assessment is not None else None,
            "recency": round(recency,1) if recency is not None else None, "consistency": round(consistency,1) if consistency is not None else None,
            "evidence": evidence_count, "last_practiced": last.isoformat() if last else None, "confidence": confidence}

def dashboard_summary(db: Session, user_id: int) -> dict:
    skills = db.query(Skill).filter_by(user_id=user_id).all()
    metrics = [(s, skill_metrics(db, s)) for s in skills]
    known = [m["health"] for _, m in metrics if m["health"] is not None]
    activities = db.query(Activity).filter_by(user_id=user_id).all()
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    week_minutes = 0
    for a in activities:
        dt = a.activity_date.replace(tzinfo=timezone.utc) if a.activity_date.tzinfo is None else a.activity_date
        if now - dt <= timedelta(days=7): week_minutes += a.duration_minutes
    return {
        "overall_health": round(sum(known)/len(known),1) if known else None,
        "active_skills": len(skills),
        "at_risk": sum(1 for _,m in metrics if m["status"] in ("At Risk","Needs Practice")),
        "practice_hours_week": round(week_minutes/60,1),
        "skills": [{"id":s.id,"name":s.name,"category":s.category,**m} for s,m in metrics],
        "recent_activities": [{"id":a.id,"title":a.title,"skill":a.skill.name,"duration_minutes":a.duration_minutes,"activity_date":a.activity_date.isoformat()} for a in sorted(activities,key=lambda x:x.activity_date,reverse=True)[:6]]
    }

def recommendations(db: Session, user_id: int) -> list[dict]:
    result = []
    for skill in db.query(Skill).filter_by(user_id=user_id).all():
        m = skill_metrics(db, skill)
        if m["health"] is None:
            result.append({"skill_id":skill.id,"skill":skill.name,"priority":"medium","title":f"Assess your {skill.name} skills","reason":"There is not enough activity or assessment data to estimate skill health.","action":"Take a short assessment and log a practice activity."})
        elif m["status"] in ("At Risk","Needs Practice"):
            result.append({"skill_id":skill.id,"skill":skill.name,"priority":"high" if m["status"]=="At Risk" else "medium","title":f"Refresh {skill.name}","reason":f"Current estimated health is {m['health']}% with status {m['status']}.","action":f"Practice {skill.name} for 30 minutes, then complete an assessment."})
        elif m["evidence"] == 0:
            result.append({"skill_id":skill.id,"skill":skill.name,"priority":"low","title":f"Add evidence for {skill.name}","reason":"No linked evidence has been recorded for this skill.","action":"Attach a relevant project, certification, or work sample."})
    return sorted(result,key=lambda r:{"high":0,"medium":1,"low":2}[r["priority"]])[:8]
