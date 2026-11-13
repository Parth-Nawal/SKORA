import json
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import User, Skill, Activity, Evidence, AssessmentQuestion
from .security import hash_password

QUESTIONS = [
("Python","Beginner","What is the result of len([1, 2, 3])?",["2","3","4","Error"],1,"The list contains three elements."),
("Python","Intermediate","Which keyword is used to define a generator function?",["return","yield","async","lambda"],1,"yield produces values lazily from a generator."),
("Python","Intermediate","What does a dictionary store?",["Only ordered numbers","Key-value pairs","Only strings","Unique list indices"],1,"Dictionaries map keys to values."),
("SQL","Beginner","Which SQL clause filters rows before grouping?",["ORDER BY","HAVING","WHERE","LIMIT"],2,"WHERE filters rows before GROUP BY."),
("SQL","Intermediate","Which JOIN returns matching rows from both tables?",["INNER JOIN","FULL JOIN","CROSS JOIN","LEFT JOIN"],0,"INNER JOIN returns rows with matching join keys."),
("Java","Beginner","Which keyword creates a subclass in Java?",["implements","extends","inherits","superclass"],1,"extends declares class inheritance."),
("Git","Beginner","Which command records staged changes in local history?",["git push","git pull","git commit","git clone"],2,"git commit creates a local commit."),
("Machine Learning","Beginner","What is overfitting?",["Model performs well on unseen data","Model learns training noise and generalizes poorly","Model has no parameters","Data is always balanced"],1,"Overfitting means poor generalization from training data."),
("Machine Learning","Intermediate","What is a validation set commonly used for?",["Final production storage","Hyperparameter/model selection","Replacing all training data","Encrypting labels"],1,"Validation data helps select models and tune parameters."),
("TensorFlow","Beginner","TensorFlow primarily supports what kind of work?",["Spreadsheet formatting","Numerical computation and machine learning","Email delivery","Version control"],1,"TensorFlow is a numerical computation and ML framework."),
("Docker","Beginner","What is a container image?",["A running process only","A packaged template used to create containers","A database table","A network cable"],1,"An image contains the filesystem and configuration used to create a container."),
("AWS","Beginner","Which AWS service provides object storage?",["EC2","S3","VPC","IAM"],1,"Amazon S3 is an object storage service."),
]

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter_by(email="demo@skora.local").first()
        if not user:
            user = User(name="Parth",email="demo@skora.local",password_hash=hash_password("SkoraDemo123!"))
            db.add(user); db.commit(); db.refresh(user)
            names = [("Python","Programming",4),("SQL","Databases",4),("Java","Programming",3),("Machine Learning","Data Science",3),("TensorFlow","Machine Learning",2),("Git","Developer Tools",4),("Docker","DevOps",2),("AWS","Cloud Computing",2)]
            for name,category,rating in names:
                db.add(Skill(user_id=user.id,name=name,category=category,self_rating=rating,target_rating=4))
            db.commit()
            skills = {s.name:s for s in db.query(Skill).filter_by(user_id=user.id).all()}
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            demo_acts = [("Python","Built a small API","Project",120,2),("Python","Practiced decorators","Practice",45,4),("SQL","Practiced JOIN queries","Practice",50,5),("Git","Reviewed branching workflow","Practice",30,3),("Machine Learning","Reviewed model evaluation","Study",60,18),("TensorFlow","Completed introductory exercise","Practice",45,32)]
            for skill,title,kind,duration,days in demo_acts:
                db.add(Activity(user_id=user.id,skill_id=skills[skill].id,title=title,activity_type=kind,duration_minutes=duration,activity_date=now-timedelta(days=days),difficulty="Intermediate"))
            e1=Evidence(user_id=user.id,title="Python API project",evidence_type="Project",description="Demo evidence record; replace with your own project.")
            e1.skills=[skills["Python"]]
            e2=Evidence(user_id=user.id,title="SQL practice portfolio",evidence_type="Project",description="Demo evidence record.")
            e2.skills=[skills["SQL"]]
            db.add_all([e1,e2]); db.commit()
        for skill,difficulty,question,options,correct,explanation in QUESTIONS:
            exists = db.query(AssessmentQuestion).filter_by(skill_name=skill,question=question).first()
            if not exists:
                db.add(AssessmentQuestion(skill_name=skill,difficulty=difficulty,question=question,options_json=json.dumps(options),correct_index=correct,explanation=explanation))
        db.commit()
        print("SKORA demo data ready. Login: demo@skora.local / SkoraDemo123!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
