"""Acceptance regressions for temporary conversational planning."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/backend'));sys.path.append(str(ROOT/'tmp/timetable-deps'))
from app.services.timetable_agent import run_chat_workflow
from app.services.timetable_conversation import parse_input, run_general, validate, schedule

DATA='''Department: Cybersecurity
Semester 1
Section A
Courses:
CYB-101 Cyber Security Fundamentals — 3 CH
CSC-101 Programming Fundamentals — 4 CH
MTH-101 Calculus — 3 CH
Teachers:
Dr. Ahmed Khan — CYB-101
Mr. Usman Ali — CSC-101
Ms. Sana Malik — MTH-101
Rooms:
Cyber Security Lab
Computing Lab
Room 301'''

CYBERSECURITY_CAPACITY_CASE='''Department: Cybersecurity
Semester: 1
Section: A

Courses:
- CYB-101 — Introduction to Cybersecurity — 3 Credit Hours
- CSC-101 — Programming Fundamentals — 4 Credit Hours
- MTH-101 — Calculus — 3 Credit Hours
- ENG-101 — Functional English — 3 Credit Hours
- ICT-101 — Introduction to Computing — 3 Credit Hours

Teachers:
- Dr. Ahmed Khan — CYB-101
- Mr. Usman Ali — CSC-101
- Ms. Sana Malik — MTH-101
- Ms. Hira Shah — ENG-101
- Mr. Bilal Ahmed — ICT-101

Available Rooms/Labs:
- Room 301
- Room 302
- Room 303
- Cyber Security Lab
- Computing Lab

Available Days:
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday

Available Time Slots:
- 09:00–10:00
- 10:00–11:00
- 11:00–12:00
- 12:00–13:00
- 14:00–15:00
- 15:00–16:00'''

MULTI_DEPARTMENT_CASE='''==================================================
DEPARTMENT OF MATHEMATICS
SEMESTER: 2
SECTION: A
==================================================
Courses:
- MTH-201 — Calculus-II — 3 Credit Hours
- MTH-202 — Linear Algebra — 3 Credit Hours
- MTH-203 — Differential Equations — 3 Credit Hours
- CSC-201 — Programming Fundamentals — 3 Credit Hours
- ENG-201 — Communication Skills — 3 Credit Hours
Teachers:
- Dr. Ali Raza — MTH-201
- Dr. Sana Ahmed — MTH-202
- Mr. Hamza Khan — MTH-203
- Mr. Usman Malik — CSC-201
- Ms. Hira Shah — ENG-201
Available Rooms:
- Math Room 201
- Math Room 202
- Computing Lab
==================================================
DEPARTMENT OF PHYSICS
SEMESTER: 2
SECTION: A
==================================================
Courses:
- PHY-201 — Mechanics-II — 3 Credit Hours
- PHY-202 — Electricity and Magnetism — 3 Credit Hours
- PHY-203 — Waves and Oscillations — 3 Credit Hours
- MTH-204 — Mathematical Methods for Physics — 3 Credit Hours
- PHY-204 — Physics Lab-II — 4 Credit Hours
Teachers:
- Dr. Farhan Ahmed — PHY-201
- Dr. Ayesha Malik — PHY-202
- Mr. Bilal Khan — PHY-203
- Dr. Sana Ahmed — MTH-204
- Mr. Kamran Ali — PHY-204
Available Rooms/Labs:
- Physics Room 301
- Physics Room 302
- Physics Lab
==================================================
AVAILABLE DAYS
==================================================
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
==================================================
AVAILABLE TIME SLOTS
==================================================
- 09:00–10:00
- 10:00–11:00
- 11:00–12:00
- 12:00–13:00
- 14:00–15:00
- 15:00–16:00'''


class NoDatabase:
    def __getattr__(self, name): raise AssertionError('General mode touched database: '+name)


class ConversationAcceptance(unittest.TestCase):
    def setUp(self):
        self.offline=patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(None,None))
        self.offline.start()
    def tearDown(self): self.offline.stop()
    def send(self, message, previous=None):
        return run_chat_workflow(NoDatabase(), {'conversation_state':json.loads(json.dumps(previous or {}))}, message)
    def test_incomplete_variants_preserve_department(self):
        for text in ['Create a timetable for Cybersecurity.', 'Generate Cybersecurity Semester 1 timetable.', 'Cybersecurity semester 1.']:
            result=self.send(text)
            self.assertEqual(result['conversation_state']['general_facts']['department'],'Cybersecurity')
            self.assertNotIn('preview_schedules',result)
            self.assertIn('teacher',result['reply'])
            self.assertEqual(result['changes'],[])
    def test_explicit_sample_only(self):
        incomplete=self.send('Generate Cybersecurity timetable.')
        self.assertNotIn('preview_schedules',incomplete)
        sample=self.send('Generate a sample/test Cybersecurity timetable yourself.')
        self.assertEqual(sample['preview_schedules'][0]['department'],'Cybersecurity')
        self.assertEqual(len(sample['preview_schedules']),9)
        self.assertNotIn('proposal_token',sample)
    def test_exact_input_and_invalid_coverage_conflicts(self):
        r=self.send(DATA); rows=r['preview_schedules']; facts=r['conversation_state']['general_facts']
        self.assertEqual(len(rows),10);self.assertEqual(validate(rows,facts),[])
        self.assertTrue(any('coverage' in e for e in validate(rows[:-1],facts)))
        corrupt=copy.deepcopy(rows);corrupt.append(dict(rows[0]))
        self.assertTrue(any('conflict' in e for e in validate(corrupt,facts)))
        for key in ['teacher','course_title','room']:
            corrupt=copy.deepcopy(rows);corrupt[0][key]='Invented value'
            self.assertTrue(validate(corrupt,facts))
    def test_edit_pronoun_and_atomic_failure(self):
        r=self.send(DATA)
        r=self.send('Move CYB-101 to Tuesday.',r['conversation_state'])
        self.assertTrue(all(x['day']=='Tuesday' for x in r['preview_schedules'] if x['course_code']=='CYB-101'))
        r=self.send('Change its teacher to Dr. Farhan.',r['conversation_state'])
        self.assertTrue(all(x['teacher']=='Dr. Farhan' for x in r['preview_schedules'] if x['course_code']=='CYB-101'))
        old=copy.deepcopy(r['conversation_state'])
        failed=self.send('Move CYB-101 to Sunday.',old)
        self.assertEqual(failed['conversation_state']['preview'],old['preview'])
        self.assertEqual(failed['conversation_state']['general_facts'],old['general_facts'])
    def test_partial_regeneration_and_global_teacher_conflicts(self):
        r=self.send(DATA)
        r=self.send('Semester 2\nCourse Code | Course Name | CH | Teacher\nCYB-201 | Network Security | 3 | Dr. Ahmed Khan',r['conversation_state'])
        old=copy.deepcopy(r['preview_schedules'])
        r=self.send('Regenerate Semester 2 only.',r['conversation_state'])
        self.assertEqual([x for x in old if x['semester']==1],[x for x in r['preview_schedules'] if x['semester']==1])
        self.assertEqual(validate(r['preview_schedules'],r['conversation_state']['general_facts']),[])
        corrupt=copy.deepcopy(r['preview_schedules'])
        a=next(x for x in corrupt if x['semester']==1 and x['teacher']=='Dr. Ahmed Khan')
        b=next(x for x in corrupt if x['semester']==2)
        for k in ['day','start_time','end_time']: b[k]=a[k]
        self.assertIn('teacher conflict',validate(corrupt,r['conversation_state']['general_facts']))
    def test_one_line_lists_and_blank_spreadsheet_cells(self):
        r=self.send('Create English Semester 1 timetable.\nCourses: ENG-1 Writing 3 CH, ENG-2 Reading 2 CH; Teachers: Ada - ENG-1, Grace - ENG-2; Rooms: Room 1, Room 2')
        self.assertEqual(len(r['preview_schedules']),5)
        facts=parse_input('Code | Course Name | CH | Teacher\nABC-101 | Algebra | | Dr. Grace')
        self.assertNotIn('credit_hours', facts['courses'][0])
        self.assertEqual(facts['courses'][0]['teacher'],'Dr. Grace')
    def test_unchanged_attachment_cannot_undo_teacher_edit(self):
        r=run_general({'document_text':DATA},'Use this.')
        r=run_general({'conversation_state':r['conversation_state'],'document_text':DATA},'Move CYB-101 to Tuesday.')
        r=run_general({'conversation_state':r['conversation_state'],'document_text':DATA},'Change its teacher to Dr. Farhan.')
        r=run_general({'conversation_state':r['conversation_state'],'document_text':DATA},'Regenerate the timetable.')
        self.assertTrue(all(x['teacher']=='Dr. Farhan' for x in r['preview_schedules'] if x['course_code']=='CYB-101'))
    def test_explicit_time_slots_and_teacher_unavailability(self):
        result=self.send('Department: English\nSemester 1\nCourse | CH | Teacher\nWriting | 3 | Dr. Ada\nTime slots: 09:30-10:30\nDr. Ada is unavailable Wednesday.')
        self.assertEqual(len(result['preview_schedules']),3)
        self.assertTrue(all(r['start_time']=='09:30' and r['day']!='Wednesday' for r in result['preview_schedules']))
    def test_model_prose_extraction_is_grounded(self):
        self.offline.stop()
        response={'department':'English','semesters':[1],'courses':[{'name':'Writing','credit_hours':3,'teacher':'Dr. Ada'}]}
        with patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(json.dumps(response),'test')):
            r=self.send('Create English Semester 1 timetable. Dr. Ada teaches Writing, which has 3 credits.')
            self.assertEqual(len(r['preview_schedules']),3)
        response['courses'][0]['teacher']='Invented Teacher'
        with patch('app.services.ai_providers.AIProviderManager.generate_chat',return_value=(json.dumps(response),'test')):
            r=self.send('Create English Semester 1 timetable. Dr. Ada teaches Writing, which has 3 credits.')
            self.assertNotIn('preview_schedules',r)
        self.offline.start()
    def test_backtracking_scheduler_handles_capacity_case_in_any_course_order(self):
        expected = {'CYB-101':3, 'CSC-101':4, 'MTH-101':3, 'ENG-101':3, 'ICT-101':3}
        variants = [CYBERSECURITY_CAPACITY_CASE]
        course_lines = [line for line in CYBERSECURITY_CAPACITY_CASE.splitlines() if line.startswith('- ') and 'Credit Hours' in line]
        for ordered in (list(reversed(course_lines)), [course_lines[4], *course_lines[:4]], [*course_lines[:1], *course_lines[2:], course_lines[1]]):
            variants.append(CYBERSECURITY_CAPACITY_CASE.replace('\n'.join(course_lines), '\n'.join(ordered)))
        for request in variants:
            result=self.send(request)
            self.assertEqual(result['changes'],[])
            self.assertIn('preview_schedules', result, result['reply'])
            rows=result['preview_schedules']; facts=result['conversation_state']['general_facts']
            self.assertEqual(len(rows),16)
            self.assertEqual({code:sum(r['course_code']==code for r in rows) for code in expected},expected)
            self.assertEqual(validate(rows,facts),[])
            self.assertTrue(all(r['day'] in ['Monday','Tuesday','Wednesday','Thursday','Friday'] for r in rows))
            self.assertTrue(all((r['start_time'],r['end_time']) in [('09:00','10:00'),('10:00','11:00'),('11:00','12:00'),('12:00','13:00'),('14:00','15:00'),('15:00','16:00')] for r in rows))
            self.assertTrue(any(r['course_code']=='ICT-101' for r in rows))
    def test_multiple_departments_use_local_rooms_and_shared_teacher_constraints(self):
        for request in (MULTI_DEPARTMENT_CASE, MULTI_DEPARTMENT_CASE.replace('\n', ' ')):
            result=self.send(request)
            self.assertEqual(result['changes'], [])
            self.assertNotIn('Please provide', result['reply'])
            self.assertIn('preview_schedules', result, result['reply'])
            rows=result['preview_schedules']; facts=result['conversation_state']['general_facts']
            self.assertEqual(len(rows), 31)
            self.assertEqual(validate(rows, facts), [])
            math=[r for r in rows if r['department']=='MATHEMATICS']
            physics=[r for r in rows if r['department']=='PHYSICS']
            self.assertEqual(len(math), 15); self.assertEqual(len(physics), 16)
            self.assertTrue(all(r['room'] in {'Math Room 201','Math Room 202','Computing Lab'} for r in math))
            self.assertTrue(all(r['room'] in {'Physics Room 301','Physics Room 302','Physics Lab'} for r in physics))
            lab=[r for r in physics if r['course_code']=='PHY-204']
            self.assertEqual(len(lab), 4)
            self.assertTrue(all(r['class_type']=='Lab' and r['room']=='Physics Lab' for r in lab))
            sana=[r for r in rows if r['teacher']=='Dr. Sana Ahmed']
            self.assertEqual(len(sana), 6)
            self.assertEqual(len({(r['day'], r['start_time']) for r in sana}), 6)
    def test_uploaded_knowledge_retrieval_and_unseen_multisection_generation(self):
        reference='''Department: Geoinformatics
Semester: 2
Course Code | Course Name | CH | Teacher | Section
GEO-201 | Spatial Databases | 3 | Dr. Naila Qureshi | A
GEO-202 | Cartographic Design | 3 | Mr. Zubair Iqbal | A
GEO-203 | Remote Sensing | 3 | Dr. Naila Qureshi | B
GEO-204 | Survey Methods | 3 | Ms. Rimsha Noor | B
Rooms:
Atlas Hall
Survey Studio'''
        generated=run_general({'document_name':'new_courses.xlsx','document_text':reference,'conversation_id':'rag-new-data'},'Generate Semester 2 timetable using the files I uploaded.')
        self.assertEqual(len(generated['preview_schedules']), 12)
        facts=generated['conversation_state']['general_facts']
        self.assertEqual(validate(generated['preview_schedules'], facts), [])
        self.assertEqual({r['section'] for r in generated['preview_schedules']}, {'A','B'})
        self.assertTrue(generated['conversation_state']['knowledge_index']['chunks'])
        answer=run_general({'conversation_state':generated['conversation_state'],'conversation_id':'rag-new-data'},'Which teacher is assigned to Spatial Databases?')
        self.assertEqual(answer['intent'], 'knowledge_answer')
        self.assertIn('Dr. Naila Qureshi', answer['reply'])
        self.assertEqual(answer['provenance']['filename'], 'new_courses.xlsx')
    def test_cross_file_relationship_normalization_and_reference_resolution(self):
        teachers='''Teacher | Teaching relationships | Availability | Preference
Dr. Nadia Khan | Machine Learning; Artificial Intelligence | Monday, Tuesday, Wednesday, Thursday | prefers morning classes
Mr. Hamza Ali | Database Systems; Data Engineering | Monday, Wednesday, Friday |'''
        courses='''Department: Data Science
Semester: 3
DST-301 Machine Learning 3 CH
DST-302 Database Systems 3 CH
Semester: 4
DST-401 Artificial Intelligence 3 CH
DST-402 Data Engineering 3 CH'''
        rooms='''Rooms:
AI Lab
Data Lab
Room 401
Constraints: practical/computing-heavy courses should prefer labs; shared teachers must never overlap; morning preference is soft, not hard.'''
        first=run_general({'document_name':'teachers.xlsx','document_text':teachers,'conversation_id':'relationship-test'},'Use this teacher file.')
        second=run_general({'conversation_state':first['conversation_state'],'document_name':'courses.pdf','document_text':courses,'conversation_id':'relationship-test'},'Use this course file.')
        generated=run_general({'conversation_state':second['conversation_state'],'document_name':'rooms.csv','document_text':rooms,'conversation_id':'relationship-test'},'Generate Semester 3 and 4 timetable using the uploaded knowledge.')
        self.assertIn('preview_schedules', generated, generated['reply'])
        rows=generated['preview_schedules']; facts=generated['conversation_state']['general_facts']
        self.assertEqual(validate(rows,facts), [])
        self.assertEqual({r['course_code']:r['teacher'] for r in rows}, {'DST-301':'Dr. Nadia Khan','DST-302':'Mr. Hamza Ali','DST-401':'Dr. Nadia Khan','DST-402':'Mr. Hamza Ali'})
        structured=generated['conversation_state']['knowledge_index']['structured']
        self.assertEqual(next(x for x in structured['teacher_availability'] if x['teacher']=='Dr. Nadia Khan')['days'], ['Monday','Tuesday','Wednesday','Thursday'])
        self.assertTrue(any(x['teacher']=='Dr. Nadia Khan' and x['value']=='morning' for x in structured['teacher_soft_preferences']))
        self.assertTrue(structured['course_room_preferences'])
        q=self.send('Who is suitable to teach AI-related courses?', generated['conversation_state'])
        self.assertEqual(q['reply'], 'Dr. Nadia Khan has the broader AI-related teaching pattern, supported by 1 explicit course relationship(s).')
        q=self.send('Which courses appear related to Dr. Nadia Khan?', generated['conversation_state'])
        self.assertIn('Machine Learning',q['reply']); self.assertIn('Artificial Intelligence',q['reply'])
        q=self.send('Which teacher has the broader AI-related teaching pattern?', generated['conversation_state'])
        self.assertIn('Dr. Nadia Khan', q['reply'])
        updated=self.send("Keep Nadia's classes earlier in the day.", generated['conversation_state'])
        self.assertEqual(updated['intent'], 'timetable_modification')
        nadia=[r for r in updated['preview_schedules'] if r['teacher']=='Dr. Nadia Khan']
        self.assertTrue(all(int(r['start_time'][:2]) < 12 for r in nadia))
        section_b=self.send('Use the same teaching pattern for another Section B timetable.', updated['conversation_state'])
        self.assertIn('preview_schedules', section_b, section_b['reply'])
        self.assertEqual(validate(section_b['preview_schedules'],section_b['conversation_state']['general_facts']), [])
        self.assertEqual(len([r for r in section_b['preview_schedules'] if r['section']=='B']), 12)
    def test_unseen_department_relationship_generalization(self):
        people='''Dr. Iman Siddiqui:
- teaches Watershed Modelling
- available Tuesday to Friday
- prefers morning classes
Mr. Owais Rafi:
- teaches Sensor Networks
- available Monday, Wednesday, Friday'''
        curriculum='''Department: Environmental Analytics
Semester: 5
EVA-501 Watershed Modelling 3 CH
EVA-502 Sensor Networks 3 CH'''
        first=run_general({'document_name':'faculty-notes.txt','document_text':people},'Use the uploaded faculty notes.')
        generated=run_general({'conversation_state':first['conversation_state'],'document_name':'curriculum.pdf','document_text':curriculum},'Create the Semester 5 timetable.')
        self.assertEqual(validate(generated['preview_schedules'],generated['conversation_state']['general_facts']), [])
        self.assertEqual({r['course_code']:r['teacher'] for r in generated['preview_schedules']}, {'EVA-501':'Dr. Iman Siddiqui','EVA-502':'Mr. Owais Rafi'})


if __name__=='__main__': unittest.main()
