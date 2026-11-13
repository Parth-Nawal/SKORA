from app.documents import extract_skills, analyze_job

def test_skill_extraction():
    found = extract_skills("I use Python, SQL, Docker and AWS.")
    assert "python" in found
    assert "sql" in found
    assert "docker" in found
    assert "aws" in found

def test_job_match_is_bounded():
    result = analyze_job("Python SQL Docker", [{"name":"Python","health":80},{"name":"SQL","health":70}])
    assert result["coverage"] == 66.7
