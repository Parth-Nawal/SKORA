from pathlib import Path
import fitz
from docx import Document

MAX_BYTES = 5 * 1024 * 1024

def extract_text(filename: str, data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds the 5 MB upload limit.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = []
        with fitz.open(stream=data, filetype="pdf") as pdf:
            for page in pdf:
                text.append(page.get_text())
        extracted = "\n".join(text).strip()
    elif suffix == ".docx":
        import io
        doc = Document(io.BytesIO(data))
        extracted = "\n".join(p.text for p in doc.paragraphs).strip()
        for table in doc.tables:
            extracted += "\n" + "\n".join(" | ".join(cell.text for cell in row.cells) for row in table.rows)
    else:
        raise ValueError("Unsupported file type. Upload a PDF or DOCX document.")
    if len(extracted) < 30:
        raise ValueError("Very little text was extracted. This may be a scanned PDF or an empty document.")
    return extracted

SKILL_ALIASES = {
    "python": ["python", "python 3"],
    "sql": ["sql", "structured query language", "mysql", "postgresql", "sqlite"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript"],
    "react": ["react", "react.js"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "machine learning": ["machine learning", "scikit-learn", "sklearn"],
    "deep learning": ["deep learning", "pytorch", "tensorflow", "keras"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "git": ["git", "github"],
    "docker": ["docker", "containerization"],
    "aws": ["aws", "amazon web services"],
    "rest apis": ["rest api", "rest apis", "restful api"],
    "opencv": ["opencv", "computer vision"],
    "data analysis": ["data analysis", "data analytics"],
    "excel": ["excel", "microsoft excel"],
}

def extract_skills(text: str) -> list[str]:
    import re
    lower = text.lower()
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9+#.])" + re.escape(alias.lower()) + r"(?![a-z0-9+#.])"
            if re.search(pattern, lower):
                found.append(canonical)
                break
    return sorted(set(found))

def analyze_job(text: str, profile_skills: list[dict]) -> dict:
    required = extract_skills(text)
    profile = {s["name"].lower(): s for s in profile_skills}
    rows = []
    for req in required:
        matching = next((s for n,s in profile.items() if n == req or req in n or n in req), None)
        rows.append({"skill":req,"status":"In profile" if matching else "Missing","health":matching.get("health") if matching else None})
    coverage = round(100 * sum(r["status"]=="In profile" for r in rows) / len(rows),1) if rows else None
    return {"required_skills":required,"coverage":coverage,"skills":rows,"note":"Coverage measures detected skill overlap only. It does not predict hiring outcomes."}
