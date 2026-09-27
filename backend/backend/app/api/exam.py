from datetime import datetime, timedelta
from io import BytesIO
import csv
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.exam import Assessment, AssessmentQuestion, AssessmentAttempt, AssessmentResponse, AssessmentTargetStudent
from app.schemas.exam import AnswerSave, ExamCreate, ExamQuestionCreate, SubmitExam, ExamViolation
from app.services.gradebook_records import FINAL_ATTEMPT_STATUSES, synchronize_course_result

router = APIRouter(tags=["Online Assessments"])
# Existing valid rosters in university.db retain "Completed" after a term
# closes; attendance and assignments already use those records. Dropped and
# withdrawn enrollments remain excluded everywhere in the exam flow.
ACTIVE_ROSTER_STATUSES = ("Enrolled", "Completed")

def _teacher(user, db):
    if user.role != "teacher": raise HTTPException(403, "Teacher access required")
    teacher = db.query(Teacher).filter(Teacher.user_id == user.user_id).first()
    if not teacher: raise HTTPException(404, "Teacher profile not found")
    return teacher

def _student(user, db):
    if user.role != "student": raise HTTPException(403, "Student access required")
    student = db.query(Student).filter(Student.user_id == user.user_id).first()
    if not student: raise HTTPException(404, "Student profile not found")
    return student

def _owned_assessment(assessment_id, teacher, db):
    assessment = db.query(Assessment).filter(Assessment.assessment_id == assessment_id, Assessment.teacher_id == teacher.teacher_id).first()
    if not assessment: raise HTTPException(404, "Assessment not found for the authenticated teacher")
    return assessment

def _enrollment_for(assessment, student, db):
    enrollment = db.query(Enrollment).filter(Enrollment.student_id == student.student_id, Enrollment.course_id == assessment.course_id, Enrollment.academic_year == assessment.academic_year, Enrollment.semester == assessment.semester, Enrollment.section == assessment.section, Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES)).first()
    if not enrollment: raise HTTPException(403, "You are not currently enrolled in this assessment's course and section")
    is_targeted = db.query(AssessmentTargetStudent).filter_by(assessment_id=assessment.assessment_id).first()
    if is_targeted and not db.query(AssessmentTargetStudent).filter_by(assessment_id=assessment.assessment_id, student_id=student.student_id).first():
        raise HTTPException(403, "This paper was not assigned to your student record")
    return enrollment

def _deadline(assessment, attempt):
    return min(assessment.end_at, attempt.started_at + timedelta(minutes=assessment.duration_minutes))

def _summary(attempt, db, reveal=False):
    rows = db.query(AssessmentResponse, AssessmentQuestion).join(AssessmentQuestion, AssessmentQuestion.question_id == AssessmentResponse.question_id).filter(AssessmentResponse.attempt_id == attempt.attempt_id).all()
    question_count = len(attempt.assessment.questions)
    correct = sum(1 for response, _ in rows if response.is_correct)
    answered = sum(1 for response, _ in rows if response.selected_option)
    result = {"attempt_id": attempt.attempt_id, "status": attempt.status, "obtained_marks": attempt.obtained_marks, "total_marks": attempt.total_marks, "percentage": round((attempt.obtained_marks / attempt.total_marks * 100) if attempt.total_marks else 0, 2), "correct_answers": correct, "incorrect_answers": max(answered - correct, 0), "unanswered_questions": question_count - answered, "submitted_at": attempt.submitted_at, "auto_submit_reason": attempt.auto_submit_reason}
    if reveal:
        result["responses"] = [{"question_id": q.question_id, "question": q.question_text, "selected_option": r.selected_option, "correct_option": q.correct_option, "is_correct": bool(r.is_correct), "awarded_marks": r.awarded_marks} for r, q in rows]
    return result

def _grade(attempt, db):
    assessment = attempt.assessment
    total = sum(question.marks for question in assessment.questions)
    earned = 0
    for question in assessment.questions:
        response = db.query(AssessmentResponse).filter_by(attempt_id=attempt.attempt_id, question_id=question.question_id).first()
        correct = bool(response and response.selected_option == question.correct_option)
        if not response:
            response = AssessmentResponse(attempt_id=attempt.attempt_id, question_id=question.question_id)
            db.add(response)
        response.is_correct = int(correct); response.awarded_marks = question.marks if correct else 0
        earned += response.awarded_marks
    attempt.obtained_marks = earned; attempt.total_marks = total
    if assessment.assessment_type in ("Midterm", "Final"):
        stable_title = f"OnlineAssessment:{assessment.assessment_id}:{assessment.title}"
        grade = db.query(Grade).filter(
            Grade.enrollment_id == attempt.enrollment_id,
            Grade.assessment_type == assessment.assessment_type,
            Grade.title == stable_title,
        ).first()
        if not grade:
            grade = db.query(Grade).filter(
                Grade.enrollment_id == attempt.enrollment_id,
                Grade.assessment_type == assessment.assessment_type,
                Grade.title == assessment.title,
            ).first()
        if not grade:
            grade = Grade(enrollment_id=attempt.enrollment_id, assessment_type=assessment.assessment_type, title=stable_title, graded_by=assessment.teacher_id, academic_year=assessment.academic_year, semester=assessment.semester)
            db.add(grade)
        grade.title = stable_title
        grade.obtained_marks = earned; grade.total_marks = total; grade.percentage = round(earned / total * 100, 2) if total else 0; grade.graded_at = datetime.utcnow(); grade.published = 1


def _sync_attempt_gradebook(attempt, db):
    db.flush()
    enrollment = db.query(Enrollment).filter_by(enrollment_id=attempt.enrollment_id).first()
    if enrollment is None:
        return None
    snapshot, _ = synchronize_course_result(db, enrollment, attempt.assessment.teacher_id)
    return snapshot

@router.get("/teacher/exams")
def teacher_exams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    teacher = _teacher(current_user, db)
    data=[]
    for a in db.query(Assessment).filter_by(teacher_id=teacher.teacher_id).order_by(Assessment.start_at.desc()).all():
        submitted=db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id==a.assessment_id, AssessmentAttempt.status != "In Progress").count()
        eligible=db.query(Enrollment).filter(Enrollment.course_id==a.course_id, Enrollment.academic_year==a.academic_year, Enrollment.semester==a.semester, Enrollment.section==a.section, Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES)).count()
        data.append({"assessment_id":a.assessment_id,"title":a.title,"type":a.assessment_type,"course_id":a.course_id,"course_code":a.course.course_code,"course_title":a.course.course_title,"section":a.section,"semester":a.semester,"academic_year":a.academic_year,"start_at":a.start_at,"end_at":a.end_at,"duration_minutes":a.duration_minutes,"total_marks":a.total_marks,"status":a.status,"question_count":len(a.questions),"submitted_count":submitted,"eligible_count":eligible})
    return {"assessments":data}

@router.get("/teacher/exams/options")
def teacher_exam_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only course sections that currently have enrolled students may receive a paper."""
    teacher = _teacher(current_user, db)
    rows = (db.query(Course, Enrollment.academic_year, Enrollment.semester, Enrollment.section)
            .join(Enrollment, Enrollment.course_id == Course.course_id)
            .filter(Course.teacher_id == teacher.teacher_id,
                    Course.status == "Active",
                    Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES),
                    Enrollment.section.isnot(None))
            .distinct()
            .order_by(Course.course_code, Enrollment.academic_year.desc())
            .all())
    courses = {}
    for course, year, semester, section in rows:
        item = courses.setdefault(course.course_id, {
            "course_id": course.course_id,
            "course_code": course.course_code,
            "course_title": course.course_title,
            "semester": course.semester,
            "sections": []
        })
        item["sections"].append({"academic_year": year, "semester": semester, "section": section, "students": []})
    if courses:
        enrolled = (db.query(Enrollment, Student)
                    .join(Student, Student.student_id == Enrollment.student_id)
                    .filter(Enrollment.course_id.in_(courses.keys()), Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES))
                    .order_by(Student.roll_number).all())
        for enrollment, student in enrolled:
            course = courses.get(enrollment.course_id)
            if not course:
                continue
            target_section = next((section for section in course["sections"] if section["academic_year"] == enrollment.academic_year and section["semester"] == enrollment.semester and section["section"] == enrollment.section), None)
            if target_section is not None:
                target_section["students"].append({"student_id": student.student_id, "name": f"{student.first_name} {student.last_name}".strip(), "roll_number": student.roll_number})
    return {"courses": list(courses.values())}

@router.post("/teacher/exams", status_code=201)
def create_exam(payload: ExamCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    teacher=_teacher(current_user, db)
    course=db.query(Course).filter(Course.course_id==payload.course_id, Course.teacher_id==teacher.teacher_id).first()
    if not course: raise HTTPException(403, "Selected course is not assigned to the authenticated teacher")
    section_enrollment = db.query(Enrollment).filter(Enrollment.course_id==course.course_id, Enrollment.academic_year==payload.academic_year, Enrollment.section==payload.section, Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES)).first()
    if not section_enrollment or section_enrollment.semester != course.semester:
        raise HTTPException(422, "No enrolled section found for the selected course and academic year")
    assessment=Assessment(course_id=course.course_id, teacher_id=teacher.teacher_id, academic_year=payload.academic_year, semester=course.semester, section=payload.section, title=payload.title.strip(), assessment_type=payload.assessment_type, start_at=payload.start_at, end_at=payload.end_at, duration_minutes=payload.duration_minutes, total_marks=payload.total_marks, status="Published" if payload.publish else "Draft")
    db.add(assessment); db.flush()
    for position,q in enumerate(payload.questions,1): db.add(AssessmentQuestion(assessment_id=assessment.assessment_id,question_text=q.question.strip(),option_a=q.option_a.strip(),option_b=q.option_b.strip(),option_c=q.option_c.strip(),option_d=q.option_d.strip(),correct_option=q.correct_option,marks=q.marks,position=position))
    if payload.student_ids:
        valid_students = {row[0] for row in db.query(Enrollment.student_id).filter(Enrollment.course_id == course.course_id, Enrollment.academic_year == payload.academic_year, Enrollment.semester == course.semester, Enrollment.section == payload.section, Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES), Enrollment.student_id.in_(set(payload.student_ids))).all()}
        requested_students = set(payload.student_ids)
        if valid_students != requested_students:
            db.rollback()
            raise HTTPException(422, "Every selected student must be currently enrolled in the selected course and section")
        for student_id in requested_students:
            db.add(AssessmentTargetStudent(assessment_id=assessment.assessment_id, student_id=student_id))
    db.commit(); return {"assessment_id":assessment.assessment_id,"status":assessment.status}

@router.post("/teacher/exams/{assessment_id}/questions/import")
async def import_questions(assessment_id:int, file:UploadFile=File(...), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    teacher=_teacher(current_user,db); assessment=_owned_assessment(assessment_id,teacher,db)
    if assessment.status == "Published": raise HTTPException(409,"Unpublish/draft the paper before importing questions")
    suffix=(file.filename or "").lower().rsplit('.',1)[-1]
    raw=await file.read()
    try:
        if suffix == "csv": rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        elif suffix == "xlsx":
            import openpyxl
            sheet=openpyxl.load_workbook(BytesIO(raw),read_only=True,data_only=True).active
            headers=[str(c.value or "").strip() for c in next(sheet.iter_rows())]
            rows=[dict(zip(headers,[c.value for c in row])) for row in sheet.iter_rows()]
        else: raise ValueError("Use a CSV or XLSX file")
    except Exception as exc: raise HTTPException(422,f"Invalid spreadsheet: {exc}")
    needed={"Question","Option A","Option B","Option C","Option D","Correct Answer","Marks"}
    if not rows or not needed.issubset(rows[0]): raise HTTPException(422,"Spreadsheet must contain: " + ", ".join(sorted(needed)))
    parsed=[]; errors=[]
    for n,row in enumerate(rows,2):
        try:
            answer=str(row["Correct Answer"]).strip().upper().replace("OPTION ","")
            if answer not in "ABCD": raise ValueError("Correct Answer must be A, B, C, or D")
            parsed.append(ExamQuestionCreate(question=str(row["Question"] or "").strip(),option_a=str(row["Option A"] or "").strip(),option_b=str(row["Option B"] or "").strip(),option_c=str(row["Option C"] or "").strip(),option_d=str(row["Option D"] or "").strip(),correct_option=answer,marks=float(row["Marks"])))
        except Exception as exc: errors.append(f"Row {n}: {exc}")
    if errors: raise HTTPException(422,{"message":"No questions saved", "errors":errors})
    # The imported question sheet is the source of truth for its total marks.
    assessment.total_marks = sum(q.marks for q in parsed)
    db.query(AssessmentQuestion).filter_by(assessment_id=assessment_id).delete()
    for position,q in enumerate(parsed,1): db.add(AssessmentQuestion(assessment_id=assessment_id,question_text=q.question,option_a=q.option_a,option_b=q.option_b,option_c=q.option_c,option_d=q.option_d,correct_option=q.correct_option,marks=q.marks,position=position))
    db.commit(); return {"imported":len(parsed)}

@router.get("/teacher/exams/overview")
def teacher_exam_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Live assessment dashboard data, restricted to the authenticated teacher."""
    teacher = _teacher(current_user, db)
    assessments = db.query(Assessment).filter_by(teacher_id=teacher.teacher_id).all()
    attempts = (db.query(AssessmentAttempt).join(Assessment)
                .filter(Assessment.teacher_id == teacher.teacher_id,
                        AssessmentAttempt.status.in_(["Submitted", "Auto Submitted"])).all())
    recent = sorted(attempts, key=lambda x: x.submitted_at or datetime.min, reverse=True)[:8]
    by_type = []
    for assessment_type in ("Quiz", "Midterm", "Final"):
        papers = [a for a in assessments if a.assessment_type == assessment_type]
        paper_ids = {a.assessment_id for a in papers}
        type_attempts = [x for x in attempts if x.assessment_id in paper_ids]
        eligible = sum(db.query(Enrollment).filter(Enrollment.course_id==a.course_id, Enrollment.academic_year==a.academic_year, Enrollment.semester==a.semester, Enrollment.section==a.section, Enrollment.enrollment_status.in_(ACTIVE_ROSTER_STATUSES)).count() for a in papers)
        average = round(sum((x.obtained_marks / x.total_marks * 100) for x in type_attempts if x.total_marks) / len(type_attempts), 2) if type_attempts else None
        by_type.append({"type": assessment_type, "assessments": len(papers), "submissions": len(type_attempts), "eligible": eligible, "average_percentage": average, "completion_rate": round((len(type_attempts) / eligible * 100) if eligible else 0, 1)})
    return {"recent_submissions": [{"student_name": f"{x.student.first_name} {x.student.last_name}", "roll_number": x.student.roll_number, "assessment_title": x.assessment.title, "submitted_at": x.submitted_at, "obtained_marks": x.obtained_marks, "total_marks": x.total_marks, "status": x.status} for x in recent], "type_overview": by_type}

@router.post("/teacher/exams/{assessment_id}/publish")
def publish_exam(assessment_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    a=_owned_assessment(assessment_id,_teacher(current_user,db),db)
    if not a.questions or abs(sum(q.marks for q in a.questions)-a.total_marks)>.01: raise HTTPException(422,"Paper requires MCQs whose marks equal total marks")
    a.status="Published"; db.commit(); return {"status":"Published"}

@router.get("/teacher/exams/{assessment_id}/results")
def teacher_results(assessment_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    a=_owned_assessment(assessment_id,_teacher(current_user,db),db); results=[]
    for x in a.attempts:
        results.append({"student_name":f"{x.student.first_name} {x.student.last_name}","roll_number":x.student.roll_number,"course":a.course.course_code,"exam_name":a.title,"exam_type":a.assessment_type,"obtained_marks":x.obtained_marks,"total_marks":x.total_marks,"percentage":round(x.obtained_marks/x.total_marks*100,2) if x.total_marks else 0,"status":x.status,"submitted_at":x.submitted_at})
    return {"results":results}

@router.get("/student/exams")
def student_exams(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    student=_student(current_user,db); now=datetime.utcnow(); items=[]
    for a in db.query(Assessment).filter_by(status="Published").order_by(Assessment.start_at).all():
        try: enrollment=_enrollment_for(a,student,db)
        except HTTPException: continue
        attempt=db.query(AssessmentAttempt).filter_by(assessment_id=a.assessment_id,student_id=student.student_id).first()
        state="Submitted" if attempt and attempt.status != "In Progress" else ("Available" if a.start_at <= now < a.end_at else ("Upcoming" if now < a.start_at else "Expired"))
        items.append({"assessment_id":a.assessment_id,"title":a.title,"type":a.assessment_type,"course":a.course.course_title,"course_code":a.course.course_code,"section":a.section,"semester":a.semester,"start_at":a.start_at,"end_at":a.end_at,"duration_minutes":a.duration_minutes,"total_marks":a.total_marks,"state":state,"attempt_id":attempt.attempt_id if attempt else None})
    return {"exams":items}

@router.post("/student/exams/{assessment_id}/start")
def start_exam(assessment_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    student=_student(current_user,db); a=db.query(Assessment).filter_by(assessment_id=assessment_id,status="Published").first()
    if not a: raise HTTPException(404,"Assessment not found")
    enrollment=_enrollment_for(a,student,db); now=datetime.utcnow()
    attempt=db.query(AssessmentAttempt).filter_by(assessment_id=a.assessment_id,student_id=student.student_id).first()
    if attempt and attempt.status != "In Progress": raise HTTPException(409,"This paper has already been submitted")
    if not attempt:
        if not a.start_at <= now < a.end_at: raise HTTPException(403,"This assessment is not currently available")
        attempt=AssessmentAttempt(assessment_id=a.assessment_id,student_id=student.student_id,enrollment_id=enrollment.enrollment_id,started_at=now,total_marks=a.total_marks);db.add(attempt);db.commit();db.refresh(attempt)
    deadline=_deadline(a,attempt)
    if now >= deadline: _grade(attempt,db);attempt.status="Auto Submitted";attempt.submitted_at=now;attempt.auto_submit_reason="timer";_sync_attempt_gradebook(attempt,db);db.commit();raise HTTPException(409,"Your attempt has expired and was submitted")
    return {"attempt_id":attempt.attempt_id,"deadline":deadline,"student":{"name":f"{student.first_name} {student.last_name}","roll_number":student.roll_number,"semester":student.semester,"section":enrollment.section},"exam":{"title":a.title,"type":a.assessment_type,"course":a.course.course_title,"course_code":a.course.course_code,"section":a.section,"total_marks":a.total_marks},"questions":[{"question_id":q.question_id,"question":q.question_text,"options":{"A":q.option_a,"B":q.option_b,"C":q.option_c,"D":q.option_d},"marks":q.marks} for q in a.questions]}

@router.patch("/student/attempts/{attempt_id}/answer")
def save_answer(attempt_id:int,payload:AnswerSave,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    student=_student(current_user,db); attempt=db.query(AssessmentAttempt).filter_by(attempt_id=attempt_id,student_id=student.student_id).first()
    if not attempt or attempt.status != "In Progress": raise HTTPException(403,"Active attempt not found")
    if datetime.utcnow() >= _deadline(attempt.assessment,attempt): raise HTTPException(409,"Attempt has expired; submit it now")
    question=db.query(AssessmentQuestion).filter_by(question_id=payload.question_id,assessment_id=attempt.assessment_id).first()
    if not question: raise HTTPException(404,"Question not found in this assessment")
    response=db.query(AssessmentResponse).filter_by(attempt_id=attempt_id,question_id=question.question_id).first()
    if not response: response=AssessmentResponse(attempt_id=attempt_id,question_id=question.question_id);db.add(response)
    response.selected_option=payload.selected_option;db.commit();return {"saved":True}

@router.post("/student/attempts/{attempt_id}/submit")
def submit_exam(attempt_id:int,payload:SubmitExam,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    student=_student(current_user,db); attempt=db.query(AssessmentAttempt).filter_by(attempt_id=attempt_id,student_id=student.student_id).first()
    if not attempt: raise HTTPException(404,"Attempt not found")
    if attempt.status != "In Progress":
        _sync_attempt_gradebook(attempt, db)
        db.commit()
        return _summary(attempt,db,True)
    now=datetime.utcnow(); expired=now>=_deadline(attempt.assessment,attempt)
    if expired and not payload.auto_submit_reason: raise HTTPException(409,"Time expired; submit as timed out")
    _grade(attempt,db);attempt.submitted_at=now;attempt.fullscreen_violations=max(attempt.fullscreen_violations,payload.fullscreen_violations);attempt.auto_submit_reason=payload.auto_submit_reason or ("timer" if expired else None);attempt.status="Auto Submitted" if attempt.auto_submit_reason else "Submitted";_sync_attempt_gradebook(attempt,db);db.commit();return _summary(attempt,db,True)

@router.post("/student/attempts/{attempt_id}/violations")
def record_exam_violation(attempt_id: int, payload: ExamViolation, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Persist a detected lockdown violation and enforce the third strike."""
    student = _student(current_user, db)
    attempt = db.query(AssessmentAttempt).filter_by(attempt_id=attempt_id, student_id=student.student_id).first()
    if not attempt or attempt.status != "In Progress":
        raise HTTPException(403, "Active attempt not found")
    attempt.fullscreen_violations = min(attempt.fullscreen_violations + 1, 3)
    if attempt.fullscreen_violations >= 3:
        _grade(attempt, db)
        attempt.status = "Auto Submitted"
        attempt.submitted_at = datetime.utcnow()
        attempt.auto_submit_reason = "fullscreen_violation"
        _sync_attempt_gradebook(attempt, db)
    db.commit()
    return {"violations": attempt.fullscreen_violations, "auto_submitted": attempt.status == "Auto Submitted"}

@router.get("/student/attempts/{attempt_id}/result")
def student_result(attempt_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    student=_student(current_user,db); attempt=db.query(AssessmentAttempt).filter_by(attempt_id=attempt_id,student_id=student.student_id).first()
    if not attempt: raise HTTPException(404,"Attempt not found")
    if attempt.status=="In Progress": raise HTTPException(403,"Results are only available after submission")
    return _summary(attempt,db,True)

@router.get("/teacher/gradebook/exam-marks")
def gradebook_marks(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    teacher=_teacher(current_user,db); records=[]
    attempts = (db.query(AssessmentAttempt).join(Assessment)
                .filter(
                    Assessment.teacher_id == teacher.teacher_id,
                    AssessmentAttempt.status.in_(FINAL_ATTEMPT_STATUSES),
                ).order_by(AssessmentAttempt.attempt_id).all())
    for attempt in attempts:
        assessment = attempt.assessment
        enrollment = db.query(Enrollment).filter_by(enrollment_id=attempt.enrollment_id).first()
        if enrollment is None:
            continue
        records.append({
            "source": "online_assessment",
            "assessment_id": assessment.assessment_id,
            "attempt_id": attempt.attempt_id,
            "enrollment_id": enrollment.enrollment_id,
            "student_id": enrollment.student_id,
            "course_id": enrollment.course_id,
            "academic_year": enrollment.academic_year,
            "semester": enrollment.semester,
            "section": enrollment.section,
            "assessment_type": assessment.assessment_type,
            "obtained_marks": attempt.obtained_marks,
            "total_marks": attempt.total_marks,
            "title": assessment.title,
            "status": attempt.status,
            "submitted_at": attempt.submitted_at,
            "auto_submit_reason": attempt.auto_submit_reason,
        })
    return {"marks":records}
