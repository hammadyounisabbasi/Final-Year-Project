"""Library integration checks: isolated DB and temporary book storage."""
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend/backend'))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.library import router
from app.core.auth import get_current_user
from app.core.database import get_db
from app.services import library_catalog as catalog

EXTERNAL={'sources':[{'title':'Neural networks','url':'https://example.org/article','kind':'Article','description':'Research'}], 'search_links':[], 'search_status':'live'}

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.patch=patch.object(catalog,'BOOKS_DIR',Path(self.folder.name));self.patch.start()
        self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        with self.engine.begin() as conn:
            raw=conn.connection
            raw.executescript('''CREATE TABLE Users(user_id INTEGER PRIMARY KEY,username TEXT);
                CREATE TABLE Departments(department_id INTEGER PRIMARY KEY,department_name TEXT);
                CREATE TABLE Students(user_id INTEGER,department_id INTEGER,first_name TEXT,last_name TEXT,roll_number TEXT);
                INSERT INTO Users VALUES (1,'admin'),(2,'student'),(3,'student2');
                INSERT INTO Departments VALUES (1,'Computer Science');
                INSERT INTO Students VALUES(2,1,'Test','Student','CS-1'),(3,1,'Second','Student','CS-2');''')
            schema=(ROOT/'database/schema/13_library.sql').read_text()
            raw.executescript(schema.split('-- TABLE: Library_Issues')[0])
            raw.executescript((ROOT/'database/migrations/v14_library_activity.sql').read_text())
        self.session=sessionmaker(bind=self.engine)
        self.user=SimpleNamespace(user_id=1,role='admin')
        app=FastAPI();app.include_router(router)
        def db():
            with self.session() as session: yield session
        app.dependency_overrides[get_db]=db
        app.dependency_overrides[get_current_user]=lambda:self.user
        self.client=TestClient(app)
    def tearDown(self):
        self.client.close();self.engine.dispose();self.patch.stop();self.folder.cleanup()
    def upload(self):
        response=self.client.post('/library/books',data={'title':'Deep Learning','author':'Test Author','category':'AI'},files={'file':('book.pdf',b'%PDF-1.4\n%%EOF','application/pdf')})
        self.assertEqual(response.status_code,201,response.text)
        return response.json()['book_id']
    def test_upload_discovery_download_and_analytics(self):
        book=self.upload();self.user=SimpleNamespace(user_id=2,role='student')
        self.assertEqual(self.client.get('/library/books').json()['books'][0]['book_id'],book)
        with patch('app.api.library.discover',return_value=EXTERNAL):
            response=self.client.post('/library/search',json={'query':'deep learning'})
        self.assertEqual(len(response.json()['books']),1)
        details=self.client.post(f'/library/books/{book}/view')
        self.assertEqual(details.status_code,200);self.assertEqual(details.json()['title'],'Deep Learning')
        self.assertEqual(details.json()['author'],'Test Author');self.assertEqual(details.json()['download_count'],0)
        for expected_downloads in (1, 2):
            r=self.client.get(f'/library/books/{book}/download');self.assertEqual(r.status_code,200);self.assertTrue(r.content.startswith(b'%PDF'))
            self.assertEqual(r.headers['x-library-download-count'], str(expected_downloads))
        summary=self.client.get('/library/analytics/summary').json()
        self.assertEqual(summary['downloads'],2);self.assertEqual(summary['top_books'][0]['book_id'],book)
        self.user=SimpleNamespace(user_id=3,role='student');self.client.get(f'/library/books/{book}/download')
        self.assertEqual(self.client.get('/library/analytics').status_code,403)
        self.user=SimpleNamespace(user_id=1,role='admin');data=self.client.get('/library/analytics').json()
        self.assertEqual(data['summary']['downloads'],3);self.assertEqual(data['summary']['downloaders'],2)
        self.assertEqual(data['summary']['searches'],1);self.assertEqual(data['departments'][0]['students'],2)
        self.assertEqual(data['interests'][0]['interest_score'],9)
    def test_upload_restrictions_and_missing_files(self):
        self.user=SimpleNamespace(user_id=2,role='student')
        self.assertEqual(self.client.post('/library/books',data={'title':'x'},files={'file':('x.pdf',b'%PDF-1.4')}).status_code,403)
        self.user=SimpleNamespace(user_id=1,role='admin')
        self.assertEqual(self.client.post('/library/books',data={'title':'x'},files={'file':('x.pdf',b'not pdf')}).status_code,422)
        self.assertEqual(list(Path(self.folder.name).iterdir()),[])
        self.assertEqual(self.client.get('/library/books/999/download').status_code,404)
        book=self.upload();next(Path(self.folder.name).glob('*.pdf')).unlink()
        self.user=SimpleNamespace(user_id=2,role='student');self.assertEqual(self.client.get(f'/library/books/{book}/download').status_code,404)
        with self.session() as db:self.assertEqual(db.execute(text('SELECT COUNT(*) FROM Library_Activity')).scalar(),0)
    def test_import_idempotent_and_paths_confined(self):
        (Path(self.folder.name)/'Python_Programming.pdf').write_bytes(b'%PDF-1.4')
        for _ in range(2):self.assertEqual(self.client.post('/library/sync').status_code,200)
        self.assertEqual(len(self.client.get('/library/books').json()['books']),1)
        with self.session() as db:
            db.execute(text("UPDATE Library SET digital_copy_path='../outside.pdf'"));db.commit()
        self.assertEqual(self.client.get('/library/books').json()['books'],[])
    def test_chat_fallback_and_history(self):
        self.upload();self.user=SimpleNamespace(user_id=2,role='student')
        with patch('app.api.library.discover',return_value=EXTERNAL), patch('app.api.library.AIProviderManager.generate_chat',return_value=(None,None)):
            response=self.client.post('/library/chat',json={'message':'deep learning articles'})
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['provider'],'Catalog fallback')
        self.assertEqual(response.json()['response'],response.json()['reply'])
        self.assertTrue(response.json()['sources']);self.assertIn('Deep Learning',response.json()['reply'])
        with patch('app.api.library.discover',return_value=EXTERNAL), patch('app.api.library.AIProviderManager.generate_chat',return_value=('Start with fundamentals','Groq')) as ai:
            response=self.client.post('/library/chat',json={'message':'which is easier?', 'history':[{'role':'user','content':'deep learning'}]})
            self.assertEqual(response.json()['provider'],'Groq');self.assertEqual(response.json()['reply'],'Start with fundamentals');self.assertIn('which is easier?',ai.call_args.args[1][-1]['content'])
        with patch('app.api.library.discover') as discovery, patch('app.api.library.AIProviderManager.generate_chat',return_value=('I help students find books.','Groq')):
            response=self.client.post('/library/chat',json={'message':'what is your role?'})
        self.assertEqual(response.status_code,200);self.assertFalse(response.json()['show_resources'])
        self.assertEqual(response.json()['books'],[]);self.assertEqual(response.json()['sources'],[])
        discovery.assert_not_called()
        self.assertEqual(self.client.post('/library/chat',json={'message':'   '}).status_code,422)

    def test_teacher_can_use_shared_catalog_and_assistant(self):
        book = self.upload()
        self.user = SimpleNamespace(user_id=4,role='teacher')
        self.assertEqual(self.client.get('/library/books').json()['books'][0]['book_id'], book)
        with patch('app.api.library.discover', return_value=EXTERNAL), patch('app.api.library.AIProviderManager.generate_chat', return_value=('Here are useful resources.', 'Groq')):
            response = self.client.post('/library/chat', json={'message':'machine learning resources'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reply'], 'Here are useful resources.')
        self.assertEqual(response.json()['provider'], 'Groq')
    def test_external_search_outage_is_explicit(self):
        from app.services.library_discovery import discover
        with patch('app.services.library_discovery.fetch',side_effect=TimeoutError):data=discover('neural networks')
        self.assertEqual(data['search_status'],'unavailable');self.assertEqual(len(data['search_links']),4)
    def test_search_html_parser_rejects_unsafe_links(self):
        from app.services.library_discovery import SearchParser
        parser=SearchParser();parser.feed('<a class="result__a" href="javascript:alert(1)">Bad</a><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fpaper">A <b>paper</b></a>')
        self.assertEqual(len(parser.results),1);self.assertEqual(parser.results[0]['url'],'https://example.org/paper')

if __name__=='__main__':unittest.main()

