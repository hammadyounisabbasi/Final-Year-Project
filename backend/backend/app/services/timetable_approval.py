"""Bind approval to the exact reviewed draft, administrator and database revision."""
import hashlib
import json
import time
from jose import jwt, JWTError
from fastapi import HTTPException
from app.core.security import SECRET_KEY, ALGORITHM
from app.models import ClassSchedule, Course, Teacher, Enrollment, Student, Department


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(',',':')).encode()).hexdigest()


def revision(db):
    # Includes historical slots and enrollment edits: concurrent publication or
    # changed capability invalidates approval rather than silently changing it.
    values = []
    for model in (ClassSchedule, Course, Teacher, Enrollment, Student, Department):
        columns = list(model.__table__.columns)
        rows = db.query(*[getattr(model,c.name) for c in columns]).order_by(columns[0]).all()
        values.append([list(row) for row in rows])
    return digest(values)


def attach_proposal(result, db, user):
    if result.get('changes'):
        current_revision = revision(db)
        if result.get('source_revision') != current_revision:
            raise HTTPException(409, 'Database changed during planning. Regenerate the proposal before reviewing it.')
        result['proposal_token'] = jwt.encode({'purpose':'timetable-approval','sub':str(user.user_id),
            'exp':int(time.time())+1800,'changes':digest(result['changes']),'revision':current_revision}, SECRET_KEY, algorithm=ALGORITHM)
    return result


def verify_proposal(token, changes, db, user):
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if claims.get('purpose') != 'timetable-approval' or claims.get('sub') != str(user.user_id): raise ValueError()
        if claims.get('changes') != digest(changes) or claims.get('revision') != revision(db): raise ValueError()
    except (JWTError, ValueError):
        raise HTTPException(409, 'Proposal expired, changed, or database changed. Regenerate and review before approving.')
