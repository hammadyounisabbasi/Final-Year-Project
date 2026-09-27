-- ===========================================================
-- FILE: 5_courses.sql
-- PURPOSE: BS COMPUTER SCIENCE COURSE DATA (INTERDISCIPLINARY & BALANCED FACULTY)
-- EXISTING COURSES TABLE: USED AS-IS
-- DUPLICATES: MANAGED WITH INSERT OR IGNORE
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- SEMESTER 1
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-101',
    'Quantitative Reasoning-I',
    'Fundamental concepts of quantitative reasoning and problem solving.',
    3,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-002') -- Ahmed Raza (Math)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-102',
    'Ideology and Constitution of Pakistan',
    'Introduction to ideology and constitutional development of Pakistan.',
    2,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') -- Sara Khan (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-103',
    'Functional English-I',
    'Development of English language communication and comprehension skills.',
    3,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-001') -- Rashid Hassan (English)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-104',
    'Civics and Community Engagement',
    'Civic responsibilities, community participation and social development.',
    2,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-005') -- Hassan Raza (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-105',
    'Entrepreneurship',
    'Fundamentals of entrepreneurship, innovation and business development.',
    2,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-BBA-005') -- Hamza Ali (BBA)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-106',
    'Applications of ICT',
    'Practical applications of information and communication technologies.',
    3,
    1,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-001') -- Rashid Minhas (IT)
);

-- ===========================================================
-- SEMESTER 2
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-201',
    'Islamic Studies',
    'Study of Islamic teachings, ethics and principles.',
    2,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') -- Sara Khan (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-202',
    'Quantitative Reasoning-II',
    'Advanced quantitative reasoning and analytical problem solving.',
    3,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-003') -- Sana Ashraf (Math)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-203',
    'Arts & Humanities',
    'Introduction to arts, humanities and cultural studies.',
    2,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-002') -- Ayesha Javed (English)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-204',
    'Natural Science',
    'Fundamental concepts of natural sciences and scientific reasoning.',
    3,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-PHY-001') -- Farhan Qureshi (Physics)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-205',
    'Social Science',
    'Introduction to social sciences and society.',
    2,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-PSY-001') -- Saba Naz (Psychology)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-206',
    'Functional English-II',
    'Advanced English communication, writing and comprehension.',
    3,
    2,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-003') -- Usman Qadir (English)
);

-- ===========================================================
-- SEMESTER 3
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-301',
    'Probability & Statistics',
    'Probability theory, statistical methods and data analysis.',
    3,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-001') -- Hina Iqbal (Math)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-302',
    'Programming Fundamentals',
    'Fundamental programming concepts, algorithms and problem solving.',
    4,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-001') -- Ahmad Malik (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-303',
    'Technical & Business Writing',
    'Technical communication, professional writing and business documentation.',
    3,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-005') -- Imran Khalid (English)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-304',
    'Digital Marketing',
    'Digital marketing concepts, strategies and online business practices.',
    3,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-BBA-003') -- Kamran Ali (BBA)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-305',
    'Digital Logic Design',
    'Digital systems, logic gates, Boolean algebra and circuit design.',
    3,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-EE-005') -- Hamid Rafiq (EE)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-306',
    'Multivariable Calculus',
    'Multivariable functions, differentiation and integration.',
    3,
    3,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-002') -- Ahmed Raza (Math)
);

-- ===========================================================
-- SEMESTER 4
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-401',
    'Linear Algebra',
    'Vectors, matrices, linear transformations and applications.',
    3,
    4,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-004') -- Kamran Awan (Math)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-402',
    'Object Oriented Programming',
    'Object-oriented programming concepts, design and implementation.',
    4,
    4,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-004') -- Fatima Noor (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-403',
    'Computer Networking',
    'Computer networks, protocols, architectures and communication.',
    3,
    4,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CY-001') -- Faisal Shah (Cyber Security)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-404',
    'Database System',
    'Database design, SQL, relational models and database management.',
    3,
    4,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-002') -- Ayesha Tariq (IT)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-405',
    'Software Engineering',
    'Software development processes, requirements and engineering practices.',
    3,
    4,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-001') -- Tariq Mehmood (SE)
);

-- ===========================================================
-- SEMESTER 5
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-501',
    'Computer Organization & Assembly Language',
    'Computer architecture, organization and assembly language programming.',
    3,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-EE-001') -- Kamran Ahmed (EE)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-502',
    'Theory of Automata',
    'Formal languages, automata, grammars and computational theory.',
    3,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-003') -- Usman Ali (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-503',
    'Operating System',
    'Operating system concepts, processes, memory and file systems.',
    3,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-005') -- Hassan Raza (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-504',
    'Information System',
    'Information systems, organizational processes and technology management.',
    3,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-003') -- Bilal Hussain (IT)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-505',
    'Web Engineering',
    'Web application development, architecture and engineering practices.',
    3,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-003') -- Farhan Ahmed (SE)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-506',
    'Data Structures & Algorithms',
    'Data structures, algorithm design and implementation.',
    4,
    5,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') -- Sara Khan (CS)
);

-- ===========================================================
-- SEMESTER 6
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-601',
    'Design & Analysis of Algorithms',
    'Algorithm design techniques, complexity analysis and optimization.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-001') -- Ahmad Malik (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-602',
    'Compiler Construction',
    'Compiler phases, parsing, lexical analysis and code generation.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-003') -- Usman Ali (CS)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-603',
    'Advanced Database System',
    'Advanced database concepts, optimization and distributed databases.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-003') -- Waqas Ali (Data Science)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-604',
    'Mobile Application Development',
    'Mobile application architecture, development and deployment.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-002') -- Hina Bilal (SE)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-605',
    'Cloud Computing',
    'Cloud infrastructure, virtualization, services and deployment models.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-004') -- Maryam Nawaz (IT)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-606',
    'Artificial Intelligence',
    'Artificial intelligence concepts, intelligent systems and problem solving.',
    3,
    6,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-001') -- Kashif Mehmood (AI)
);

-- ===========================================================
-- SEMESTER 7
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-701',
    'Final Year Project-I',
    'Research, planning and initial development of the final year project.',
    3,
    7,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-001') -- Tariq Mehmood (SE)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-702',
    'Machine Learning',
    'Machine learning algorithms, model development and evaluation.',
    3,
    7,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-003') -- Zeeshan Qureshi (AI)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-703',
    'Internet of Things',
    'IoT architecture, sensors, communication and intelligent devices.',
    3,
    7,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CY-003') -- Hamza Tariq (Cyber Security)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-704',
    'Big Data',
    'Big data concepts, distributed processing and analytics.',
    3,
    7,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-001') -- Kamran Malik (Data Science)
);

-- ===========================================================
-- SEMESTER 8
-- ===========================================================

INSERT OR IGNORE INTO Courses
(department_id, course_code, course_title, course_description,
 credit_hours, semester, course_type, teacher_id)
VALUES
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-801',
    'Final Year Project-II',
    'Implementation, evaluation, documentation and final defense of FYP.',
    3,
    8,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-001') -- Kamran Malik (Data Science)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-802',
    'Deep Learning',
    'Deep neural networks, optimization and deep learning applications.',
    3,
    8,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-002') -- Asma Bibi (AI)
),
(
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'CSE-803',
    'Neural Networks',
    'Neural network architectures, training and practical applications.',
    3,
    8,
    'Core',
    (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-005') -- Ali Raza (AI)
);

-- ===========================================================
-- VERIFICATION
-- ===========================================================

SELECT
    semester,
    COUNT(*) AS course_count
FROM Courses
WHERE department_id = (
    SELECT department_id
    FROM Departments
    WHERE department_code = 'CSE'
)
GROUP BY semester
ORDER BY semester;

-- ===========================================================
-- TOTAL
-- ===========================================================

SELECT COUNT(*) AS total_cse_courses
FROM Courses
WHERE department_id = (
    SELECT department_id
    FROM Departments
    WHERE department_code = 'CSE'
);