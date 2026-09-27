"""Read-only timetable constraints and reusable, evidence-based teacher ranking."""
from collections import defaultdict
from types import SimpleNamespace
import re

from app.models import ClassSchedule, Course, Teacher, Enrollment, Department

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOTS = [(f'{hour:02}:00', f'{hour+1:02}:00') for hour in range(8, 17)]
FIELDS = ('course_id', 'teacher_id', 'academic_year', 'semester', 'section',
          'day_of_week', 'start_time', 'end_time', 'room_location', 'class_type')


def minutes(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
        raise ValueError('Time must use HH:MM')
    hour, minute = map(int, value.split(':'))
    return hour * 60 + minute


class ConstraintSnapshot:
    def __init__(self, db):
        self.db = db
        self.courses = {c.course_id: c for c in db.query(Course).all()}
        self.teachers = {t.teacher_id: t for t in db.query(Teacher).all()}
        self.rows = db.query(ClassSchedule).filter_by(status='Active').all()
        self.all_rows = db.query(ClassSchedule).all()
        self.rooms = sorted({r.room_location.strip() for r in self.rows if r.room_location.strip()})
        self.students = defaultdict(set)
        self.cohorts = defaultdict(set)
        self.enrollments = db.query(Enrollment).filter_by(enrollment_status='Enrolled').all()
        for e in self.enrollments:
            key = (e.course_id, e.academic_year, e.semester, e.section)
            self.students[key].add(e.student_id)
            self.cohorts[key].add(e.student.department_id)

    @staticmethod
    def key(row):
        return row.course_id, row.academic_year, row.semester, row.section

    @staticmethod
    def course_signature(course):
        """Database-safe equivalence key for a course shared by two departments."""
        title = re.sub(r'[^a-z0-9]+', '', course.course_title.casefold())
        return title, int(course.credit_hours)

    def reference_course_structure(self, source_department_id, target_department_id, semester):
        """Map a requested reference structure onto *target* course records.

        A reference never authorises scheduling the source department's course IDs.
        This method deliberately requires an existing target course with the same
        title and credit hours, so an administrator can see the exact missing
        course mapping instead of receiving an empty or misleading proposal.
        """
        source = sorted((course for course in self.courses.values()
                         if course.status == 'Active' and course.department_id == source_department_id
                         and (not semester or course.semester == semester)), key=lambda c: c.course_code)
        target = sorted((course for course in self.courses.values()
                         if course.status == 'Active' and course.department_id == target_department_id
                         and (not semester or course.semester == semester)), key=lambda c: c.course_code)
        by_signature = defaultdict(list)
        for course in target:
            by_signature[self.course_signature(course)].append(course)
        mappings, unmapped = [], []
        for course in source:
            candidates = by_signature[self.course_signature(course)]
            if len(candidates) == 1:
                mappings.append((course, candidates[0]))
            else:
                unmapped.append(course)
        serialize = lambda c: {'course_id': c.course_id, 'code': c.course_code,
                               'title': c.course_title, 'credit_hours': c.credit_hours}
        return {'source_courses': [serialize(c) for c in source],
                'target_courses': [serialize(c) for c in target],
                'mappings': [{'source': serialize(left), 'target': serialize(right)} for left, right in mappings],
                'unmapped_source_courses': [serialize(c) for c in unmapped],
                'target_course_ids': [right.course_id for _, right in mappings]}

    def conflicts(self, left, right):
        if left.academic_year != right.academic_year or left.day_of_week != right.day_of_week:
            return []
        if not (left.start_time < right.end_time and left.end_time > right.start_time):
            return []
        reasons = []
        if left.teacher_id == right.teacher_id: reasons.append('Teacher conflict')
        if left.room_location.strip().casefold() == right.room_location.strip().casefold(): reasons.append('Room conflict')
        a, b = self.key(left), self.key(right)
        # Section A in two different departments is not the same cohort.
        da = self.cohorts[a] or {self.courses[left.course_id].department_id}
        db = self.cohorts[b] or {self.courses[right.course_id].department_id}
        if (left.semester, left.section) == (right.semester, right.section) and da & db:
            reasons.append('Section conflict')
        if self.students[a] & self.students[b]: reasons.append('Student conflict')
        return reasons

    def teacher_matches(self, course, year, staged=(), requested=None, ignore_ids=(), eligibility_only=False):
        matches = []
        title = course.course_title.casefold()
        for teacher in self.teachers.values():
            if teacher.status != 'Active' or (requested and teacher.teacher_id not in requested): continue
            assigned = [c for c in self.courses.values() if c.teacher_id == teacher.teacher_id and c.status == 'Active']
            owned = course.teacher_id == teacher.teacher_id
            same = any(c.course_title.casefold() == title for c in assigned)
            expertise = title in (teacher.specialization or '').casefold()
            if not (owned or same or expertise): continue
            rows = [r for r in [*self.rows, *staged] if r.teacher_id == teacher.teacher_id and r.academic_year == year and getattr(r,'schedule_id',None) not in ignore_ids]
            hours = sum((minutes(r.end_time) - minutes(r.start_time)) / 60 for r in rows)
            if hours >= 18 and not eligibility_only: continue
            distinct = {r.course_id for r in rows}
            if course.course_id not in distinct and len(distinct) >= 6 and not eligibility_only: continue
            evidence = 'existing course assignment' if owned else 'matching taught course' if same else 'recorded specialization'
            matches.append((hours, not owned, teacher.department_id != course.department_id, len(assigned), teacher.teacher_id,
                            f'{evidence}; {hours:g} scheduled hours this year, {len(distinct)} scheduled courses and {len(assigned)} recorded course assignments'))
        return sorted(matches)

    def validate(self, changes):
        errors, staged, seen = [], [], set()
        updates = {c.get('schedule_id') for c in changes if c.get('action') == 'update'}
        live = [r for r in self.rows if r.schedule_id not in updates]
        for index, change in enumerate(changes):
            reasons = []
            try:
                row = SimpleNamespace(**{k: change[k] for k in FIELDS})
                course, teacher = self.courses.get(row.course_id), self.teachers.get(row.teacher_id)
                if not course or not teacher or course.status != 'Active' or teacher.status != 'Active':
                    raise ValueError('Invalid active course or teacher')
                if change.get('action') not in ('create', 'update'): raise ValueError('Invalid action')
                if not isinstance(row.semester, int) or not 1 <= row.semester <= 20: raise ValueError('Invalid semester')
                if row.day_of_week not in DAYS or row.class_type not in ('Lecture', 'Lab', 'Tutorial', 'Seminar'): raise ValueError('Invalid day or class type')
                if minutes(row.end_time) - minutes(row.start_time) != 60: raise ValueError('Sessions must be one hour')
                if row.room_location not in self.rooms: raise ValueError('Room is not in recorded inventory')
                if row.class_type == 'Lab' and not re.search(r'\blab(?:oratory)?\b', row.room_location, re.I):
                    raise ValueError('Practical session requires a recorded lab')
                if not self.students[self.key(row)]: raise ValueError('No matching enrolled students')
                assigned = [c for c in self.courses.values() if c.teacher_id == teacher.teacher_id and c.status == 'Active']
                if not (course.teacher_id == teacher.teacher_id or any(c.course_title.casefold() == course.course_title.casefold() for c in assigned) or course.course_title.casefold() in (teacher.specialization or '').casefold()):
                    raise ValueError('No eligible teacher capability or workload capacity')
                identity = (*self.key(row), row.day_of_week, row.start_time)
                if identity in seen: raise ValueError('Duplicate proposal')
                seen.add(identity)
                if any((*self.key(r), r.day_of_week, r.start_time) == identity for r in self.all_rows):
                    raise ValueError('Existing or historical entry already occupies this course slot')
                if change['action'] == 'update':
                    current = next((r for r in self.rows if r.schedule_id == change.get('schedule_id')), None)
                    if not current or change.get('before') != {k: getattr(current, k) for k in FIELDS}:
                        raise ValueError('Replacement is stale or missing its original record')
                    if self.key(current) != self.key(row): raise ValueError('Replacement cannot change enrollment scope')
                for other in [*live, *staged]: reasons.extend(self.conflicts(row, other))
                hours = sum((minutes(r.end_time)-minutes(r.start_time))/60 for r in [*live, *staged, row]
                            if r.teacher_id == row.teacher_id and r.academic_year == row.academic_year)
                if hours > 18: reasons.append('Teacher exceeds 18 scheduled hours')
                distinct = {r.course_id for r in [*live,*staged,row] if r.teacher_id == row.teacher_id and r.academic_year == row.academic_year}
                if len(distinct) > 6: reasons.append('Teacher exceeds 6 scheduled courses')
                staged.append(row)
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                reasons.append(str(exc))
            if reasons: errors.append({'index': index, 'reasons': sorted(set(reasons))})
        return errors

    def validate_coverage(self, changes):
        """Validate final weekly minutes, never an incremental candidate prefix."""
        updated = {c.get('schedule_id') for c in changes if c.get('action') == 'update'}
        rows = [r for r in self.rows if r.schedule_id not in updated]
        rows += [SimpleNamespace(**{k: c[k] for k in FIELDS}) for c in changes]
        errors = []
        for key in {self.key(SimpleNamespace(**c)) for c in changes}:
            course = self.courses[key[0]]
            minutes_scheduled = sum(minutes(r.end_time)-minutes(r.start_time) for r in rows if self.key(r) == key)
            if minutes_scheduled != int(course.credit_hours)*60:
                errors.append({'reasons': [f'{course.course_code}: weekly duration must equal {course.credit_hours} credit hours']})
        return errors

    def plan(self, scope, attempt=0):
        changes, warnings, handled = [], [], set()
        targets = []
        for enrollment in self.enrollments:
            course = self.courses[enrollment.course_id]
            if course.status != 'Active': continue
            if scope.get('department_id') and enrollment.student.department_id != scope['department_id']: continue
            if any(scope.get(k) and getattr(enrollment, k) != scope[k] for k in ('semester', 'section', 'academic_year', 'student_id')): continue
            if scope.get('semesters') and enrollment.semester not in scope['semesters']: continue
            if scope.get('course_ids') and course.course_id not in scope['course_ids']: continue
            key = self.key(enrollment)
            if key not in handled: targets.append((enrollment, course)); handled.add(key)
        # A teacher view constrains candidate teachers, never silently broadens scope.
        requested = scope.get('teacher_ids') or ([scope['teacher_id']] if scope.get('teacher_id') else None)
        for enrollment, course in sorted(targets, key=lambda pair: (-pair[1].credit_hours, pair[1].course_id)):
            old = [r for r in self.rows if self.key(r) == self.key(enrollment)]
            missing = max(0, int(course.credit_hours) - len(old))
            replace = scope.get('replace', False)
            work = [*old, *([None] * missing)] if replace else [None] * missing
            for position, current in enumerate(work):
                found = None
                staged = [SimpleNamespace(**{k: c[k] for k in FIELDS}) for c in changes]
                replaced_ids = [c['schedule_id'] for c in changes if c['action']=='update']
                if current: replaced_ids.append(current.schedule_id)
                for match in self.teacher_matches(course, enrollment.academic_year, staged, requested, replaced_ids):
                    hours, _, _, _, teacher_id, reason = match
                    used_days = [r.day_of_week for r in [*old, *staged] if r.course_id == course.course_id]
                    days = sorted(DAYS, key=lambda d: (used_days.count(d), (DAYS.index(d)+attempt) % len(DAYS)))
                    for day in days:
                        if day in scope.get('avoid_days', []): continue
                        for start, end in SLOTS:
                            if scope.get('start_after') and start < scope['start_after']: continue
                            if scope.get('end_before') and end > scope['end_before']: continue
                            for room in self.rooms:
                                candidate = dict(action='update' if current else 'create', course_id=course.course_id,
                                    teacher_id=teacher_id, academic_year=enrollment.academic_year, semester=enrollment.semester,
                                    section=enrollment.section, day_of_week=day, start_time=start, end_time=end,
                                    room_location=room, class_type=current.class_type if current else ('Lab' if course.credit_hours == 4 and (position if replace else len(old)+position) == 3 else 'Lecture'),
                                    reason=reason, before={k:getattr(current,k) for k in FIELDS} if current else None)
                                if current:
                                    candidate['schedule_id'] = current.schedule_id
                                    if all(candidate[k] == getattr(current,k) for k in FIELDS): continue
                                if not self.validate([*changes, candidate]): found = candidate; break
                            if found: break
                        if found: break
                    if found: break
                if found: changes.append(found)
                else: warnings.append(f'{course.course_code}, semester {enrollment.semester}, section {enrollment.section}: no eligible teacher and conflict-free slot within the workload/availability constraints.')
        if not targets:
            department = self.db.get(Department, scope['department_id']) if scope.get('department_id') else None
            label = department.department_name if department else 'The selected scope'
            if scope.get('semester'): label += f" Semester {scope['semester']}"
            active_courses = [c for c in self.courses.values() if c.status == 'Active'
                              and (not scope.get('department_id') or c.department_id == scope['department_id'])
                              and (not scope.get('semester') or c.semester == scope['semester'])]
            warnings.append(f'{label} has no active course records in the database.' if not active_courses else
                            f'{label} has no matching active enrollments. Review course mappings and enrollment records.')
        for semester in scope.get('semesters', []):
            if not any(e.semester == semester for e, _ in targets):
                warnings.append(f'Semester {semester} has no matching active enrolled courses in the requested database scope.')
        if not self.rooms: warnings.append('No recorded teaching rooms are available.')
        return changes, list(dict.fromkeys(warnings))
