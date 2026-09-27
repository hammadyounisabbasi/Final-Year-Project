-- ===========================================================
-- FILE: 02_departments.sql
-- PURPOSE: University of Haripur Departments
-- PROJECT: Virtual University Database
-- ===========================================================

PRAGMA foreign_keys = ON;

INSERT INTO Departments
(
    department_code,
    department_name,
    department_short_name,
    office_location,
    office_phone,
    office_email,
    hod_user_id,
    status
)
VALUES

-- ===========================================================
-- Faculty of Computing
-- ===========================================================

('CSE',
'Department of Computer Science',
'Computer Science',
'Academic Block A - Ground Floor',
'+92-995-920101',
'cse@uoh.edu.pk',
NULL,
'Active'),

('SE',
'Department of Software Engineering',
'Software Engineering',
'Academic Block A - First Floor',
'+92-995-920102',
'se@uoh.edu.pk',
NULL,
'Active'),

('IT',
'Department of Information Technology',
'Information Technology',
'Academic Block A - Second Floor',
'+92-995-920103',
'it@uoh.edu.pk',
NULL,
'Active'),

('AI',
'Department of Artificial Intelligence',
'Artificial Intelligence',
'Innovation Block - First Floor',
'+92-995-920104',
'ai@uoh.edu.pk',
NULL,
'Active'),

('CY',
'Department of Cyber Security',
'Cyber Security',
'Innovation Block - Second Floor',
'+92-995-920105',
'cyber@uoh.edu.pk',
NULL,
'Active'),

('DS',
'Department of Data Science',
'Data Science',
'Innovation Block - Third Floor',
'+92-995-920106',
'datascience@uoh.edu.pk',
NULL,
'Active'),

-- ===========================================================
-- Faculty of Engineering
-- ===========================================================

('CE',
'Department of Civil Engineering',
'Civil Engineering',
'Engineering Block',
'+92-995-920201',
'civil@uoh.edu.pk',
NULL,
'Active'),

('EE',
'Department of Electrical Engineering',
'Electrical Engineering',
'Engineering Block',
'+92-995-920202',
'ee@uoh.edu.pk',
NULL,
'Active'),

('ME',
'Department of Mechanical Engineering',
'Mechanical Engineering',
'Engineering Block',
'+92-995-920203',
'me@uoh.edu.pk',
NULL,
'Active'),

-- ===========================================================
-- Faculty of Management
-- ===========================================================

('BBA',
'Department of Business Administration',
'Business Administration',
'Management Block',
'+92-995-920301',
'bba@uoh.edu.pk',
NULL,
'Active'),

('ECO',
'Department of Economics',
'Economics',
'Management Block',
'+92-995-920302',
'economics@uoh.edu.pk',
NULL,
'Active'),

('COM',
'Department of Commerce',
'Commerce',
'Management Block',
'+92-995-920303',
'commerce@uoh.edu.pk',
NULL,
'Active'),

-- ===========================================================
-- Faculty of Sciences
-- ===========================================================

('MTH',
'Department of Mathematics',
'Mathematics',
'Science Block',
'+92-995-920401',
'math@uoh.edu.pk',
NULL,
'Active'),

('PHY',
'Department of Physics',
'Physics',
'Science Block',
'+92-995-920402',
'physics@uoh.edu.pk',
NULL,
'Active'),

('CHE',
'Department of Chemistry',
'Chemistry',
'Science Block',
'+92-995-920403',
'chemistry@uoh.edu.pk',
NULL,
'Active'),

-- ===========================================================
-- Faculty of Social Sciences
-- ===========================================================

('ENG',
'Department of English',
'English',
'Humanities Block',
'+92-995-920501',
'english@uoh.edu.pk',
NULL,
'Active'),

('PSY',
'Department of Psychology',
'Psychology',
'Humanities Block',
'+92-995-920502',
'psychology@uoh.edu.pk',
NULL,
'Active'),

('EDU',
'Department of Education',
'Education',
'Humanities Block',
'+92-995-920503',
'education@uoh.edu.pk',
NULL,
'Active'),

-- ===========================================================
-- Faculty of Life Sciences
-- ===========================================================

('BIO',
'Department of Biotechnology',
'Biotechnology',
'Life Sciences Block',
'+92-995-920601',
'biotech@uoh.edu.pk',
NULL,
'Active'),

('ENV',
'Department of Environmental Sciences',
'Environmental Sciences',
'Life Sciences Block',
'+92-995-920602',
'environment@uoh.edu.pk',
NULL,
'Active');

-- ===========================================================
-- SUMMARY
-- ===========================================================
-- Total Departments : 20
-- HOD Assignment    : Pending (03_teachers.sql)
-- Status            : Active
-- ===========================================================
