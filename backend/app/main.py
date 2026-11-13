import json, os, secrets
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, get_db
from .models import User, Skill, Activity, Evidence, AssessmentQuestion, AssessmentAttempt
from .schemas import (
    RegisterIn, LoginIn, SkillIn, ActivityIn, EvidenceIn,
    AssessmentSubmit, JobAnalyzeIn, ProfileIn,
    AIQuizGenerateIn, AIQuizSubmitIn,
)
from .security import hash_password, verify_password, create_token, decode_token
from .scoring import skill_metrics, dashboard_summary, recommendations
from .documents import extract_text, extract_skills, analyze_job


Base.metadata.create_all(bind=engine)
app = FastAPI(title="SKORA API", version="1.0.0", description="Personal Skill Intelligence Platform")
origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    user_id = decode_token(authorization.split(" ",1)[1])
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user

@app.get("/api/health")
def health():
    return {"status":"ok","service":"SKORA API"}

@app.post("/api/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(func.lower(User.email)==email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token":create_token(user.id),"token_type":"bearer","user":{"id":user.id,"name":user.name,"email":user.email}}

@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email)==payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token":create_token(user.id),"token_type":"bearer","user":{"id":user.id,"name":user.name,"email":user.email}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id":user.id,"name":user.name,"email":user.email}

@app.put("/api/profile")
def update_profile(payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.name = payload.name.strip(); db.commit()
    return {"id":user.id,"name":user.name,"email":user.email}

@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return dashboard_summary(db,user.id)

@app.get("/api/skills")
def list_skills(user: User = Depends(current_user), db: Session = Depends(get_db)):
    skills = db.query(Skill).filter_by(user_id=user.id).order_by(Skill.name).all()
    return [{"id":s.id,"name":s.name,"category":s.category,"self_rating":s.self_rating,"target_rating":s.target_rating,**skill_metrics(db,s)} for s in skills]

@app.post("/api/skills", status_code=201)
def create_skill(payload: SkillIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.query(Skill).filter_by(user_id=user.id, name=payload.name.strip()).first():
        raise HTTPException(409,"This skill is already in your profile")
    s = Skill(user_id=user.id,name=payload.name.strip(),category=payload.category,self_rating=payload.self_rating,target_rating=payload.target_rating)
    db.add(s); db.commit(); db.refresh(s)
    return {"id":s.id,"name":s.name,"category":s.category,"self_rating":s.self_rating,"target_rating":s.target_rating,**skill_metrics(db,s)}

@app.get("/api/skills/{skill_id}")
def skill_detail(skill_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.query(Skill).filter_by(id=skill_id,user_id=user.id).first()
    if not s: raise HTTPException(404,"Skill not found")
    acts = db.query(Activity).filter_by(skill_id=s.id,user_id=user.id).order_by(Activity.activity_date.desc()).limit(20).all()
    attempts = db.query(AssessmentAttempt).filter_by(skill_id=s.id,user_id=user.id).order_by(AssessmentAttempt.completed_at.desc()).limit(10).all()
    return {"id":s.id,"name":s.name,"category":s.category,"self_rating":s.self_rating,"target_rating":s.target_rating,**skill_metrics(db,s),
            "activities":[{"id":a.id,"title":a.title,"description":a.description,"duration_minutes":a.duration_minutes,"activity_type":a.activity_type,"difficulty":a.difficulty,"activity_date":a.activity_date.isoformat()} for a in acts],
            "attempts":[{"id":a.id,"score":a.score,"total":a.total,"percentage":a.percentage,"completed_at":a.completed_at.isoformat()} for a in attempts]}

@app.delete("/api/skills/{skill_id}")
def delete_skill(skill_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.query(Skill).filter_by(id=skill_id,user_id=user.id).first()
    if not s: raise HTTPException(404,"Skill not found")
    db.delete(s); db.commit()
    return {"deleted":True}

@app.get("/api/activities")
def list_activities(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Activity).filter_by(user_id=user.id).order_by(Activity.activity_date.desc()).limit(100).all()
    return [{"id":a.id,"skill_id":a.skill_id,"skill":a.skill.name,"title":a.title,"description":a.description,"activity_type":a.activity_type,"duration_minutes":a.duration_minutes,"difficulty":a.difficulty,"score":a.score,"activity_date":a.activity_date.isoformat()} for a in rows]

@app.post("/api/activities", status_code=201)
def create_activity(payload: ActivityIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skill = db.query(Skill).filter_by(id=payload.skill_id,user_id=user.id).first()
    if not skill: raise HTTPException(404,"Skill not found")
    a = Activity(user_id=user.id,**payload.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return {"id":a.id,"title":a.title,"skill":skill.name,"duration_minutes":a.duration_minutes,"activity_date":a.activity_date.isoformat()}

@app.get("/api/evidence")
def list_evidence(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Evidence).filter_by(user_id=user.id).order_by(Evidence.created_at.desc()).all()
    return [{"id":e.id,"title":e.title,"evidence_type":e.evidence_type,"description":e.description,"url":e.url,"skills":[{"id":s.id,"name":s.name} for s in e.skills]} for e in rows]

@app.post("/api/evidence", status_code=201)
def create_evidence(payload: EvidenceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ids = set(payload.skill_ids)
    skills = db.query(Skill).filter(Skill.user_id==user.id, Skill.id.in_(ids)).all() if ids else []
    if len(skills) != len(ids): raise HTTPException(400,"One or more skills are invalid")
    e = Evidence(user_id=user.id,title=payload.title.strip(),evidence_type=payload.evidence_type,description=payload.description,url=payload.url)
    e.skills = skills
    db.add(e); db.commit(); db.refresh(e)
    return {"id":e.id,"title":e.title,"evidence_type":e.evidence_type,"skills":[s.name for s in skills]}

@app.delete("/api/evidence/{evidence_id}")
def delete_evidence(evidence_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    e = db.query(Evidence).filter_by(id=evidence_id,user_id=user.id).first()
    if not e: raise HTTPException(404,"Evidence not found")
    db.delete(e); db.commit()
    return {"deleted":True}

@app.get("/api/assessments")
def list_assessments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    names = db.query(AssessmentQuestion.skill_name).distinct().all()
    output = []
    for (name,) in names:
        questions = db.query(AssessmentQuestion).filter_by(skill_name=name).count()
        skill = db.query(Skill).filter_by(user_id=user.id,name=name).first()
        latest = db.query(AssessmentAttempt).filter_by(user_id=user.id,skill_id=skill.id).order_by(AssessmentAttempt.completed_at.desc()).first() if skill else None
        output.append({"skill_name":name,"question_count":questions,"last_score":latest.percentage if latest else None,"skill_id":skill.id if skill else None})
    return output

@app.get("/api/assessments/{skill_name}")
def assessment_questions(skill_name: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    questions = db.query(AssessmentQuestion).filter(func.lower(AssessmentQuestion.skill_name)==skill_name.lower()).all()
    if not questions: raise HTTPException(404,"No assessment available for this skill")
    return [{"id":q.id,"skill_name":q.skill_name,"difficulty":q.difficulty,"question":q.question,"options":json.loads(q.options_json)} for q in questions]




# Temporary server-side storage for AI-generated quizzes.
# This is suitable for local demos; quizzes are lost on restart.
_ai_quizzes = {}


@app.post("/api/assessments/ai/generate")
def generate_ai_assessment(
    payload: AIQuizGenerateIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    from .ai_quiz import generate_quiz

    skill = db.query(Skill).filter_by(
        id=payload.skill_id,
        user_id=user.id,
    ).first()

    if not skill:
        raise HTTPException(404, "Skill not found in your profile")

    try:
        questions = generate_quiz(
            skill_name=skill.name,
            difficulty=payload.difficulty,
            topic=payload.topic,
            count=payload.count,
        )
    except Exception as exc:
        # Log the details in the backend terminal, not to the client.
        print(f"AI quiz generation failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            502,
            "AI quiz generation failed. Check the backend terminal and API quota.",
        ) from exc

    quiz_id = secrets.token_urlsafe(24)

    # Store the answer key on the server, never return it to the frontend.
    _ai_quizzes[quiz_id] = {
        "user_id": user.id,
        "skill_id": skill.id,
        "questions": questions,
    }

    return {
        "quiz_id": quiz_id,
        "skill_id": skill.id,
        "skill_name": skill.name,
        "difficulty": payload.difficulty,
        "topic": payload.topic or skill.name,
        "questions": [
            {
                "id": index,
                "question": question["question"],
                "options": question["options"],
            }
            for index, question in enumerate(questions, start=1)
        ],
    }


@app.post("/api/assessments/ai/submit")
def submit_ai_assessment(
    payload: AIQuizSubmitIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    quiz = _ai_quizzes.get(payload.quiz_id)

    if not quiz or quiz["user_id"] != user.id:
        raise HTTPException(
            404,
            "Quiz not found or expired. Generate a new quiz.",
        )

    questions = quiz["questions"]

    if not payload.answers:
        raise HTTPException(400, "No answers submitted")

    valid_ids = set(range(1, len(questions) + 1))

    if any(qid not in valid_ids for qid in payload.answers):
        raise HTTPException(400, "Invalid question ID")

    if any(
        not isinstance(answer, int)
        or isinstance(answer, bool)
        or answer not in range(4)
        for answer in payload.answers.values()
    ):
        raise HTTPException(400, "Each answer must be an option index from 0 to 3")

    correct = sum(
        1
        for qid, answer in payload.answers.items()
        if questions[qid - 1]["correct_index"] == answer
    )
    total = len(payload.answers)

    attempt = AssessmentAttempt(
        user_id=user.id,
        skill_id=quiz["skill_id"],
        score=correct,
        total=total,
        percentage=round(correct / total * 100, 1),
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    explanations = [
        {
            "question_id": qid,
            "correct": questions[qid - 1]["correct_index"] == answer,
            "correct_index": questions[qid - 1]["correct_index"],
            "explanation": questions[qid - 1]["explanation"],
        }
        for qid, answer in payload.answers.items()
    ]

    # Prevent the same quiz from being submitted repeatedly.
    del _ai_quizzes[payload.quiz_id]

    return {
        "id": attempt.id,
        "score": correct,
        "total": total,
        "percentage": attempt.percentage,
        "explanations": explanations,
    }


@app.post("/api/assessments/{skill_id}/submit")
def submit_assessment(skill_id: int, payload: AssessmentSubmit, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skill = db.query(Skill).filter_by(id=skill_id,user_id=user.id).first()
    if not skill: raise HTTPException(404,"Skill not found. Add this skill to your profile first.")
    questions = db.query(AssessmentQuestion).filter(func.lower(AssessmentQuestion.skill_name)==skill.name.lower()).all()
    if not questions: raise HTTPException(404,"No assessment available for this skill")
    by_id = {q.id:q for q in questions}
    if any(qid not in by_id for qid in payload.answers): raise HTTPException(400,"Invalid question ID")
    if not payload.answers: raise HTTPException(400,"No answers submitted")
    correct = sum(1 for qid,ans in payload.answers.items() if by_id[qid].correct_index == ans)
    total = len(payload.answers)
    attempt = AssessmentAttempt(user_id=user.id,skill_id=skill.id,score=correct,total=total,percentage=round(correct/total*100,1))
    db.add(attempt); db.commit(); db.refresh(attempt)
    explanations = [{"question_id":qid,"correct":by_id[qid].correct_index==ans,"correct_index":by_id[qid].correct_index,"explanation":by_id[qid].explanation} for qid,ans in payload.answers.items()]
    return {"id":attempt.id,"score":correct,"total":total,"percentage":attempt.percentage,"explanations":explanations}

@app.post("/api/resume/analyze")
async def resume_analyze(file: UploadFile = File(...), user: User = Depends(current_user)):
    data = await file.read()
    try:
        text = extract_text(file.filename or "resume.pdf", data)
    except ValueError as exc:
        raise HTTPException(400,str(exc))
    found = extract_skills(text)
    sections = {}
    lower = text.lower()
    for label, aliases in {"Education":["education","academic"],"Experience":["experience","employment","internship"],"Projects":["projects","project"],"Skills":["skills","technical skills"],"Certifications":["certifications","certificates"]}.items():
        sections[label] = any(alias in lower for alias in aliases)
    return {"filename":Path(file.filename or "resume").name,"character_count":len(text),"skills_detected":found,"sections":sections,"missing_sections":[k for k,v in sections.items() if not v],"preview":text[:1200],"note":"Rule-based document analysis. A detected skill is not proof of proficiency."}

@app.post("/api/jobs/analyze")
def job_analyze(payload: JobAnalyzeIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    skills = db.query(Skill).filter_by(user_id=user.id).all()
    profile = [{"name":s.name,**skill_metrics(db,s)} for s in skills]
    result = analyze_job(payload.description,profile)
    result["title"] = payload.title
    return result

@app.get("/api/recommendations")
def get_recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return recommendations(db,user.id)
