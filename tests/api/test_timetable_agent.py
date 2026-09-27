"""Integration checks using an in-memory SQLite backup of the real university DB.

No fake university records are created and the source database is never written.
Run: python -m unittest discover -s tests/api -p test_timetable_agent.py -v
"""
import copy
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/backend'))
# Optional dependencies installed locally by the validation environment.
sys.path.append(str(ROOT/'tmp/timetable-deps'))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.models import User, ClassSchedule, Course, Enrollment, StudentTimetable, Teacher
from app.core.database import get_db
from app.core.auth import get_current_user
from app.api.admin import router as admin_router
from app.api.student import get_student_timetable
from app.api.teacher import get_teacher_schedule
from app.services.timetable_constraints import ConstraintSnapshot, FIELDS
from app.services.timetable_creator import run_generation_workflow, run_chat_workflow
from app.services.timetable_approval import attach_proposal, revision
from app.services.timetable_documents import extract_document_text, extract_reference_facts, build_timetable_pdf


def real_database_copy():
    # Separate connections share one memory-only backup, matching production's
    # connection ownership and avoiding StaticPool cursor races across requests.
    from uuid import uuid4
    from sqlalchemy import event
    from sqlalchemy.pool import QueuePool
    uri=f'file:timetable-{uuid4().hex}?mode=memory&cache=shared'
    keeper=sqlite3.connect(uri,uri=True,check_same_thread=False)
    source=sqlite3.connect(f'file:{(ROOT/"database/university.db").as_posix()}?mode=ro',uri=True)
    source.backup(keeper);source.close()
    def connect():
        connection=sqlite3.connect(uri,uri=True,check_same_thread=False,timeout=30)
        connection.execute('PRAGMA foreign_keys=ON')
        return connection
    engine=create_engine('sqlite://',creator=connect,poolclass=QueuePool)
    event.listen(engine,'engine_disposed',lambda ignored:keeper.close())
    return engine, sessionmaker(bind=engine,expire_on_commit=False)


class TimetableIntegration(unittest.TestCase):
    def setUp(self):
        self.engine, factory=real_database_copy();self.db=factory()
        self.user=self.db.query(User).filter_by(role='admin').first()
        self.app=FastAPI();self.app.include_router(admin_router)
        self.app.dependency_overrides[get_db]=lambda:self.db
        self.app.dependency_overrides[get_current_user]=lambda:self.user
        self.client=TestClient(self.app)
        self.offline=patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(None,None));self.offline.start()

    def tearDown(self): self.offline.stop();self.db.close();self.engine.dispose()

    def draft(self):
        return run_generation_workflow(self.db,{'department_id':1,'semester':1,'section':'A'},'Replace Computer Science Semester 1 Section A timetable')

    def test_graph_read_only_replacement_and_validation(self):
        before=revision(self.db);result=self.draft()
        self.assertTrue(result['changes'],result['warning'])
        self.assertEqual(before,revision(self.db))
        self.assertEqual(result['workflow_steps'][-1],'await_admin_approval')
        self.assertLess(result['workflow_steps'].index('read_database'),result['workflow_steps'].index('generate_proposal'))
        self.assertFalse(ConstraintSnapshot(self.db).validate(result['changes']))
        self.assertTrue(all(c['before'] for c in result['changes']))

    def test_text_only_and_unknown_future_department(self):
        for prompt in ['Generate Software Engineering Semester 1 timetable.','Generate Environmental Sciences Semester 1 timetable.']:
            response=self.client.post('/admin/timetable-creator/chat',json={'message':prompt})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['conversation_state']['general_facts']['semesters'],[1])
            self.assertEqual(response.json()['changes'],[])
            self.assertNotIn('preview_schedules',response.json())

    def test_followup_workload_and_cross_department_scope(self):
        response=self.client.post('/admin/timetable-creator/chat',json={'department_id':1,'message':'Analyze teacher workload using university database'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.json()['agent_context']['teachers'])
        self.assertIn('sessions',response.json()['reply'])
        from app.services.timetable_creator import infer_request_scope
        scope=infer_request_scope(self.db,{'department_id':2},'Use the same first-semester subjects as CS.')
        self.assertEqual(scope['department_id'],2)
        self.assertEqual(scope['source_department_id'],1)
        self.assertEqual(scope['semester'],1)

    def test_cross_department_request_reports_real_target_prerequisites(self):
        prompt=('Generate a timetable for Software Engineering 1st Semester Section A '
                'using the same course structure as Computer Science 1st Semester.')
        result=run_generation_workflow(self.db,{},prompt)
        self.assertEqual(result['scope']['department_id'],2)
        self.assertEqual(result['scope']['source_department_id'],1)
        self.assertEqual(result['scope']['semester'],1)
        self.assertEqual(result['scope']['section'],'A')
        self.assertEqual(result['changes'],[])
        self.assertEqual(result['approval_state'],'blocked')
        self.assertTrue(result['reference_course_structure']['source_courses'])
        self.assertEqual(result['reference_course_structure']['target_courses'],[])
        self.assertIn('target department has no active courses',result['ai_explanation'])
        self.assertNotIn('Prepared 0 validated timetable changes',result['ai_explanation'])
        self.assertNotIn('repair_conflicts',result['workflow_steps'])

    def test_conversational_routing_and_read_only_general_preview(self):
        greeting=run_chat_workflow(self.db,{},'Hi, are you able to generate a timetable for me?')
        self.assertEqual(greeting['intent'],'capability')
        self.assertNotIn('blocked',greeting['reply'].casefold())
        general=run_chat_workflow(self.db,{'history':[{'role':'user','content':'I just want a general test timetable.'}]},'For Software Engineering Semester 1.')
        self.assertEqual(general['mode'],'general')
        self.assertIn('courses',general['reply'].casefold())
        result=run_chat_workflow(self.db,{'history':[{'role':'user','content':'I just want a general test timetable.'},{'role':'user','content':'For Software Engineering Semester 1.'}]},'Courses:\nSE-101 Programming Fundamentals 3 CH\nSE-102 Calculus 3 CH\nTeachers:\nAda - SE-101\nGrace - SE-102\nRooms:\nLab 1\nRoom 2')
        self.assertEqual(result['intent'],'general_generation')
        self.assertEqual(result['changes'],[])
        self.assertEqual(result['approval_state'],'general_preview')
        self.assertEqual(len(result['preview_schedules']),6)
        self.assertEqual(result['preview_schedules'][0]['department'],'Software Engineering')
        self.assertEqual(result['preview_schedules'][0]['semester'],1)
        self.assertNotIn('proposal_token',result)

    def test_explicit_system_prompt_routes_to_database_workflow(self):
        result=run_chat_workflow(self.db,{},'Generate the actual timetable for our CS Semester 1 students using the database.')
        self.assertEqual(result['intent'],'system_generation')
        self.assertEqual(result['mode'],'system')
        self.assertEqual(result['scope']['semester'],1)

    def test_latest_system_department_does_not_inherit_reference_curriculum(self):
        result=run_chat_workflow(self.db,{'department_id':1,'history':[
            {'role':'user','content':'Generate actual CS Semester 1 using university database.'},
            {'role':'user','content':'Generate actual Software Engineering Semester 1 using university database.'}]},
            'Generate actual Software Engineering Semester 1 using university database.')
        self.assertEqual(result['scope']['department_id'],2)
        self.assertFalse(result['scope'].get('source_department_id'))
        self.assertIn('Software Engineering Semester 1 has no active course records',result['reply'])

    def test_incomplete_pasted_schedule_is_not_accepted_as_credit_coverage(self):
        result=run_chat_workflow(self.db,{}, 'General timetable for English Semester 1.\nCourses:\nENG-101 Functional English 3 CH')
        self.assertEqual(result['changes'],[])
        self.assertNotIn('preview_schedules',result)
        self.assertIn('assigned teacher',result['reply'])

    def test_reviewed_file_text_feeds_general_generation_without_database_matching(self):
        scope={'document_text': 'Department: English\nSemester 1\nCourse Code | Course Name | CH | Teacher\nENG-101 | Functional English | 3 | Dr. Ayesha Khan'}
        result=run_chat_workflow(self.db,scope,'Generate using this file.')
        self.assertEqual(result['mode'],'general')
        self.assertEqual(result['changes'],[])
        self.assertEqual(len(result['preview_schedules']),3)
        self.assertEqual(result['preview_schedules'][0]['course_code'],'ENG-101')

    def test_approval_requires_exact_proof_and_updates_both_portals(self):
        result=attach_proposal(self.draft(),self.db,self.user)
        payload={'changes':result['changes'],'proposal_token':result['proposal_token'],'approved':True}
        missing=dict(payload);missing.pop('approved')
        self.assertEqual(self.client.post('/admin/timetable-creator/approve',json=missing).status_code,422)
        tampered=copy.deepcopy(payload);tampered['changes'][0]['room_location']='Not a real room'
        self.assertEqual(self.client.post('/admin/timetable-creator/approve',json=tampered).status_code,409)
        response=self.client.post('/admin/timetable-creator/approve',json=payload)
        self.assertEqual(response.status_code,200,response.text)
        created=response.json()['created'];self.assertTrue(created)
        for row in created:
            schedule=self.db.get(ClassSchedule,row['schedule_id'])
            links=self.db.query(StudentTimetable).filter_by(schedule_id=schedule.schedule_id).all()
            self.assertTrue(links)
            student=links[0].student
            portal=get_student_timetable(semester=schedule.semester,current_user=student.user,db=self.db)
            self.assertIn(str(schedule.schedule_id),str(portal['timetable_grid']))
            teacher=self.db.get(Teacher,schedule.teacher_id)
            portal=get_teacher_schedule(course_id=None,academic_year=None,semester=None,schedule_status='Active',current_user=teacher.user,db=self.db)
            self.assertIn(schedule.schedule_id,[r['schedule_id'] for r in portal['schedules']])
        self.assertEqual(self.client.post('/admin/timetable-creator/approve',json=payload).status_code,409)
        self.assertTrue(all(self.db.get(ClassSchedule,c['schedule_id']).status=='Cancelled' for c in payload['changes']))

    def test_pdf_is_real_text_and_document_facts(self):
        result=self.draft();pdf=build_timetable_pdf(result['preview_schedules'])
        text=extract_document_text('misleading-file-name.pdf',pdf.getvalue())
        self.assertIn('University Timetable',text);self.assertIn('Teacher:',text)
        facts=extract_reference_facts(self.db,text);self.assertTrue(facts['courses']);self.assertTrue(facts['teachers'])
        upload=self.client.post('/admin/timetable-creator/document',files={'document':('reference.pdf',pdf.getvalue(),'application/pdf')})
        self.assertEqual(upload.status_code,200,upload.text);self.assertFalse(upload.json()['needs_review'])
        out=ROOT/'tmp/timetable-preview-test.pdf';out.write_bytes(pdf.getvalue())

    def test_malformed_file_and_unauthorized(self):
        self.assertEqual(self.client.post('/admin/timetable-creator/document',files={'document':('broken.pdf',b'broken','application/pdf')}).status_code,422)
        student=self.db.query(User).filter_by(role='student').first()
        self.app.dependency_overrides[get_current_user]=lambda:student
        self.assertEqual(self.client.post('/admin/timetable-creator/chat',json={'message':'Generate timetable'}).status_code,403)

    def test_constraint_rejection(self):
        result=self.draft();change=copy.deepcopy(result['changes'][0]);change['start_time']='25:00'
        self.assertTrue(ConstraintSnapshot(self.db).validate([change]))
        change=copy.deepcopy(result['changes'][0]);change['teacher_id']=999999
        self.assertTrue(ConstraintSnapshot(self.db).validate([change]))

    def test_missing_session_is_created_without_unsolicited_replacements(self):
        enrollment=self.db.query(Enrollment).filter_by(enrollment_status='Enrolled',semester=1).first()
        old=self.db.query(ClassSchedule).filter_by(course_id=enrollment.course_id,academic_year=enrollment.academic_year,semester=enrollment.semester,section=enrollment.section,status='Active').first()
        self.assertIsNotNone(old)
        old.status='Cancelled';self.db.commit()
        scope={'department_id':enrollment.student.department_id,'semester':enrollment.semester,'section':enrollment.section,'academic_year':enrollment.academic_year}
        result=run_generation_workflow(self.db,scope,'Generate timetable')
        self.assertTrue(any(c['course_id']==enrollment.course_id for c in result['changes']),result['warning'])
        self.assertTrue(all(c['action']=='create' for c in result['changes']))

    def test_independent_conflicts_and_workload_ranking(self):
        from types import SimpleNamespace
        snapshot=ConstraintSnapshot(self.db);original=snapshot.rows[0]
        other=SimpleNamespace(**{key:getattr(original,key) for key in FIELDS})
        other.teacher_id=next(t for t in snapshot.teachers if t!=original.teacher_id)
        self.assertIn('Room conflict',snapshot.conflicts(original,other))
        other.teacher_id=original.teacher_id
        other.room_location=next(r for r in snapshot.rooms if r!=original.room_location)
        self.assertIn('Teacher conflict',snapshot.conflicts(original,other))
        self.assertIn('Student conflict',snapshot.conflicts(original,other))
        matches=snapshot.teacher_matches(snapshot.courses[original.course_id],original.academic_year)
        self.assertEqual(matches,sorted(matches))
        self.assertTrue(all(m[0]<18 for m in matches))

    def test_bounded_repair_branch(self):
        from app.services import timetable_agent as agent
        original=agent.validate
        calls=[]
        def validate_once_stale(state):
            result=original(state);calls.append(1)
            if len(calls)==1: result['errors']=[{'index':0,'reasons':['Simulated changed booking']}]
            return result
        with patch.object(agent,'validate',validate_once_stale):
            result=agent.build_workflow().invoke({'db':self.db,'scope':{'department_id':1,'semester':1},'prompt':'Replace timetable','history':[],'document_text':'','attempt':0})
        self.assertIn('repair_conflicts',result['trace'])
        self.assertEqual(len(calls),2)
        self.assertFalse(result['errors'])

    def test_offline_unknown_subject_list_does_not_broaden_scope(self):
        result=run_generation_workflow(self.db,{'department_id':1,'semester':1},'Generate timetable using subjects: Unrecorded Course')
        self.assertFalse(result['changes'])
        self.assertIn('No exact active database match',result['warning'])

    def test_reviewed_reference_and_history_contract(self):
        response=self.client.post('/admin/timetable-creator/chat',json={'message':'Generate timetable','document_text':'Course information'})
        self.assertEqual(response.status_code,422)
        response=self.client.post('/admin/timetable-creator/chat',json={'message':'Generate timetable','history':[{'role':'user','content':None}]})
        self.assertEqual(response.status_code,422)

    def test_explicit_scope_and_time_constraints(self):
        result=run_generation_workflow(self.db,{'department_id':2,'semester':2},'Replace Computer Science Semester 1 timetable. Mornings only.')
        self.assertEqual(result['scope']['department_id'],1)
        self.assertEqual(result['scope']['semester'],1)
        self.assertEqual(result['scope']['end_before'],'12:00')
        self.assertTrue(all(c['end_time']<='12:00' for c in result['changes']))

    def test_revision_change_during_planning_blocks_signing(self):
        from fastapi import HTTPException
        result=self.draft()
        course=self.db.get(Course,result['changes'][0]['course_id'])
        course.credit_hours=course.credit_hours+1
        self.db.commit()
        with self.assertRaises(HTTPException) as caught:
            attach_proposal(result,self.db,self.user)
        self.assertEqual(caught.exception.status_code,409)

    def test_concurrent_approval_only_commits_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from types import SimpleNamespace
        result=attach_proposal(self.draft(),self.db,self.user)
        payload={'changes':result['changes'],'proposal_token':result['proposal_token'],'approved':True}
        # Authentication fixture must not share an expiring ORM instance across threads.
        principal=SimpleNamespace(user_id=self.user.user_id, role=self.user.role)
        self.app.dependency_overrides[get_current_user]=lambda:principal
        self.db.rollback()
        factory=sessionmaker(bind=self.engine,expire_on_commit=False)
        def request_session():
            session=factory()
            try: yield session
            finally: session.close()
        self.app.dependency_overrides[get_db]=request_session
        before=self.db.query(ClassSchedule).count()
        self.db.rollback()
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses=list(executor.map(lambda _:self.client.post('/admin/timetable-creator/approve',json=payload),range(2)))
        self.assertEqual(sorted(r.status_code for r in responses),[200,409])
        self.assertEqual(self.db.query(ClassSchedule).count(),before+len(payload['changes']))

    def test_provider_fallback_order(self):
        from app.services.ai_providers import AIProviderManager
        manager=AIProviderManager();visited=[]
        for index,provider in enumerate(manager.providers):
            provider.is_configured=lambda:True
            def respond(*args,i=index,p=provider):
                visited.append(p.name)
                if i<3: raise RuntimeError('Controlled provider outage')
                return 'valid result'
            provider.generate=respond
        self.offline.stop()
        with patch('app.services.ai_providers.reload_environment'):
            result=manager.generate_chat('test',[{'role':'user','content':'test'}])
        self.assertEqual(visited,['Groq','Gemini','Hugging Face','Ollama'])
        self.assertEqual(result[0],'valid result')
        self.offline.start()


if __name__=='__main__': unittest.main()
