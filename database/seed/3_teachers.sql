-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 1
-- DEPARTMENT: COMPUTER SCIENCE
-- PURPOSE: Create User Accounts for CS Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- COMPUTER SCIENCE - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'ahmad.malik',
'ahmad.malik@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sara.khan',
'sara.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'usman.ali',
'usman.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'fatima.noor',
'fatima.noor@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hassan.raza',
'hassan.raza@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 2
-- DEPARTMENT: COMPUTER SCIENCE
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- COMPUTER SCIENCE TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'ahmad.malik'),
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'UOH-CSE-001',
    'Ahmad',
    'Malik',
    'Male',
    '1982-04-15',
    '03001234001',
    'ahmad.malik@uoh.edu.pk',
    'Professor',
    'PhD Computer Science',
    'Artificial Intelligence',
    '2010-09-01',
    'AB-A101',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'sara.khan'),
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'UOH-CSE-002',
    'Sara',
    'Khan',
    'Female',
    '1986-07-22',
    '03001234002',
    'sara.khan@uoh.edu.pk',
    'Associate Professor',
    'PhD Computer Science',
    'Machine Learning',
    '2014-02-17',
    'AB-A102',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'usman.ali'),
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'UOH-CSE-003',
    'Usman',
    'Ali',
    'Male',
    '1988-10-11',
    '03001234003',
    'usman.ali@uoh.edu.pk',
    'Assistant Professor',
    'MS Computer Science',
    'Database Systems',
    '2018-08-20',
    'AB-A103',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'fatima.noor'),
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'UOH-CSE-004',
    'Fatima',
    'Noor',
    'Female',
    '1990-03-09',
    '03001234004',
    'fatima.noor@uoh.edu.pk',
    'Lecturer',
    'MS Computer Science',
    'Software Engineering',
    '2020-01-15',
    'AB-A104',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'hassan.raza'),
    (SELECT department_id FROM Departments WHERE department_code = 'CSE'),
    'UOH-CSE-005',
    'Hassan',
    'Raza',
    'Male',
    '1992-12-05',
    '03001234005',
    'hassan.raza@uoh.edu.pk',
    'Lecturer',
    'MS Computer Science',
    'Computer Networks',
    '2022-09-05',
    'AB-A105',
    'Permanent',
    'Active'
);

-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 3
-- DEPARTMENT: SOFTWARE ENGINEERING
-- PURPOSE: Create User Accounts for SE Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- SOFTWARE ENGINEERING - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'farhan.ahmed',
'farhan.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'ayesha.siddiqui',
'ayesha.siddiqui@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'kamran.shah',
'kamran.shah@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'mariam.aslam',
'mariam.aslam@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'bilal.abbas',
'bilal.abbas@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 4
-- DEPARTMENT: SOFTWARE ENGINEERING
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- SOFTWARE ENGINEERING TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'farhan.ahmed'),
    (SELECT department_id FROM Departments WHERE department_code = 'SE'),
    'UOH-SE-001',
    'Farhan',
    'Ahmed',
    'Male',
    '1983-06-18',
    '03001235001',
    'farhan.ahmed@uoh.edu.pk',
    'Professor',
    'PhD Software Engineering',
    'Software Architecture',
    '2011-08-15',
    'AB-B101',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'ayesha.siddiqui'),
    (SELECT department_id FROM Departments WHERE department_code = 'SE'),
    'UOH-SE-002',
    'Ayesha',
    'Siddiqui',
    'Female',
    '1987-01-12',
    '03001235002',
    'ayesha.siddiqui@uoh.edu.pk',
    'Associate Professor',
    'PhD Software Engineering',
    'Software Testing & QA',
    '2015-02-20',
    'AB-B102',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'kamran.shah'),
    (SELECT department_id FROM Departments WHERE department_code = 'SE'),
    'UOH-SE-003',
    'Kamran',
    'Shah',
    'Male',
    '1989-09-25',
    '03001235003',
    'kamran.shah@uoh.edu.pk',
    'Assistant Professor',
    'MS Software Engineering',
    'DevOps & Cloud Computing',
    '2018-09-01',
    'AB-B103',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'mariam.aslam'),
    (SELECT department_id FROM Departments WHERE department_code = 'SE'),
    'UOH-SE-004',
    'Mariam',
    'Aslam',
    'Female',
    '1991-04-08',
    '03001235004',
    'mariam.aslam@uoh.edu.pk',
    'Lecturer',
    'MS Software Engineering',
    'Requirements Engineering',
    '2021-01-10',
    'AB-B104',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'bilal.abbas'),
    (SELECT department_id FROM Departments WHERE department_code = 'SE'),
    'UOH-SE-005',
    'Bilal',
    'Abbas',
    'Male',
    '1993-11-30',
    '03001235005',
    'bilal.abbas@uoh.edu.pk',
    'Lecturer',
    'MS Software Engineering',
    'Agile Software Development',
    '2023-02-06',
    'AB-B105',
    'Permanent',
    'Active'
);

-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 5
-- DEPARTMENT: INFORMATION TECHNOLOGY
-- PURPOSE: Create User Accounts for IT Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- INFORMATION TECHNOLOGY - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'naveed.akram',
'naveed.akram@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'iqra.waheed',
'iqra.waheed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'zohaib.ahmad',
'zohaib.ahmad@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hira.ali',
'hira.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'waqas.khalid',
'waqas.khalid@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 5 SUMMARY
-- ===========================================================
-- Department : Information Technology
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 6)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 6
-- DEPARTMENT: INFORMATION TECHNOLOGY
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- INFORMATION TECHNOLOGY TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'naveed.akram'),
    (SELECT department_id FROM Departments WHERE department_code = 'IT'),
    'UOH-IT-001',
    'Naveed',
    'Akram',
    'Male',
    '1982-05-14',
    '03001236001',
    'naveed.akram@uoh.edu.pk',
    'Professor',
    'PhD Information Technology',
    'Computer Networks',
    '2010-08-18',
    'AB-C101',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'iqra.waheed'),
    (SELECT department_id FROM Departments WHERE department_code = 'IT'),
    'UOH-IT-002',
    'Iqra',
    'Waheed',
    'Female',
    '1988-10-22',
    '03001236002',
    'iqra.waheed@uoh.edu.pk',
    'Associate Professor',
    'PhD Information Technology',
    'Cloud Computing',
    '2014-09-01',
    'AB-C102',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'zohaib.ahmad'),
    (SELECT department_id FROM Departments WHERE department_code = 'IT'),
    'UOH-IT-003',
    'Zohaib',
    'Ahmad',
    'Male',
    '1990-03-09',
    '03001236003',
    'zohaib.ahmad@uoh.edu.pk',
    'Assistant Professor',
    'MS Information Technology',
    'Database Systems',
    '2018-02-15',
    'AB-C103',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'hira.ali'),
    (SELECT department_id FROM Departments WHERE department_code = 'IT'),
    'UOH-IT-004',
    'Hira',
    'Ali',
    'Female',
    '1992-07-18',
    '03001236004',
    'hira.ali@uoh.edu.pk',
    'Lecturer',
    'MS Information Technology',
    'Web Technologies',
    '2021-08-30',
    'AB-C104',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'waqas.khalid'),
    (SELECT department_id FROM Departments WHERE department_code = 'IT'),
    'UOH-IT-005',
    'Waqas',
    'Khalid',
    'Male',
    '1994-01-11',
    '03001236005',
    'waqas.khalid@uoh.edu.pk',
    'Lecturer',
    'MS Information Technology',
    'Information Security',
    '2023-01-16',
    'AB-C105',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 6 SUMMARY
-- ===========================================================
-- Department : Information Technology
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Part)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 7
-- DEPARTMENT: ARTIFICIAL INTELLIGENCE
-- PURPOSE: Create User Accounts for AI Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ARTIFICIAL INTELLIGENCE - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'hamid.raza',
'hamid.raza@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'ayesha.noor',
'ayesha.noor@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'usman.shah',
'usman.shah@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'zainab.farooq',
'zainab.farooq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'bilal.ahmed',
'bilal.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 7 SUMMARY
-- ===========================================================
-- Department : Artificial Intelligence
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 8)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 8
-- DEPARTMENT: ARTIFICIAL INTELLIGENCE
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ARTIFICIAL INTELLIGENCE TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'hamid.raza'),
    (SELECT department_id FROM Departments WHERE department_code = 'AI'),
    'UOH-AI-001',
    'Hamid',
    'Raza',
    'Male',
    '1981-04-18',
    '03001237001',
    'hamid.raza@uoh.edu.pk',
    'Professor',
    'PhD Artificial Intelligence',
    'Machine Learning',
    '2011-08-15',
    'IB-201',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'ayesha.noor'),
    (SELECT department_id FROM Departments WHERE department_code = 'AI'),
    'UOH-AI-002',
    'Ayesha',
    'Noor',
    'Female',
    '1987-09-09',
    '03001237002',
    'ayesha.noor@uoh.edu.pk',
    'Associate Professor',
    'PhD Artificial Intelligence',
    'Deep Learning',
    '2015-09-01',
    'IB-202',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'usman.shah'),
    (SELECT department_id FROM Departments WHERE department_code = 'AI'),
    'UOH-AI-003',
    'Usman',
    'Shah',
    'Male',
    '1990-12-11',
    '03001237003',
    'usman.shah@uoh.edu.pk',
    'Assistant Professor',
    'MS Artificial Intelligence',
    'Natural Language Processing',
    '2019-02-18',
    'IB-203',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'zainab.farooq'),
    (SELECT department_id FROM Departments WHERE department_code = 'AI'),
    'UOH-AI-004',
    'Zainab',
    'Farooq',
    'Female',
    '1992-06-27',
    '03001237004',
    'zainab.farooq@uoh.edu.pk',
    'Lecturer',
    'MS Artificial Intelligence',
    'Computer Vision',
    '2022-01-10',
    'IB-204',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'bilal.ahmed'),
    (SELECT department_id FROM Departments WHERE department_code = 'AI'),
    'UOH-AI-005',
    'Bilal',
    'Ahmed',
    'Male',
    '1993-08-03',
    '03001237005',
    'bilal.ahmed@uoh.edu.pk',
    'Lecturer',
    'MS Artificial Intelligence',
    'Generative AI & LLMs',
    '2023-08-21',
    'IB-205',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 8 SUMMARY
-- ===========================================================
-- Department : Artificial Intelligence
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 9
-- DEPARTMENT: CYBER SECURITY
-- PURPOSE: Create User Accounts for Cyber Security Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CYBER SECURITY - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'kamran.yousaf',
'kamran.yousaf@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'iqra.aslam',
'iqra.aslam@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'saad.waqar',
'saad.waqar@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'maryam.khalid',
'maryam.khalid@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'junaid.abbas',
'junaid.abbas@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 9 SUMMARY
-- ===========================================================
-- Department : Cyber Security
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 10)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 10
-- DEPARTMENT: CYBER SECURITY
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CYBER SECURITY TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'kamran.yousaf'),
    (SELECT department_id FROM Departments WHERE department_code = 'CY'),
    'UOH-CY-001',
    'Kamran',
    'Yousaf',
    'Male',
    '1982-05-14',
    '03001238001',
    'kamran.yousaf@uoh.edu.pk',
    'Professor',
    'PhD Cyber Security',
    'Network Security',
    '2010-09-01',
    'IB-301',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'iqra.aslam'),
    (SELECT department_id FROM Departments WHERE department_code = 'CY'),
    'UOH-CY-002',
    'Iqra',
    'Aslam',
    'Female',
    '1988-07-22',
    '03001238002',
    'iqra.aslam@uoh.edu.pk',
    'Associate Professor',
    'PhD Information Security',
    'Digital Forensics',
    '2014-08-18',
    'IB-302',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'saad.waqar'),
    (SELECT department_id FROM Departments WHERE department_code = 'CY'),
    'UOH-CY-003',
    'Saad',
    'Waqar',
    'Male',
    '1990-03-11',
    '03001238003',
    'saad.waqar@uoh.edu.pk',
    'Assistant Professor',
    'MS Cyber Security',
    'Ethical Hacking',
    '2018-09-03',
    'IB-303',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'maryam.khalid'),
    (SELECT department_id FROM Departments WHERE department_code = 'CY'),
    'UOH-CY-004',
    'Maryam',
    'Khalid',
    'Female',
    '1992-10-05',
    '03001238004',
    'maryam.khalid@uoh.edu.pk',
    'Lecturer',
    'MS Cyber Security',
    'Cloud Security',
    '2021-01-15',
    'IB-304',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'junaid.abbas'),
    (SELECT department_id FROM Departments WHERE department_code = 'CY'),
    'UOH-CY-005',
    'Junaid',
    'Abbas',
    'Male',
    '1994-01-27',
    '03001238005',
    'junaid.abbas@uoh.edu.pk',
    'Lecturer',
    'MS Information Security',
    'Penetration Testing',
    '2023-02-20',
    'IB-305',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 10 SUMMARY
-- ===========================================================
-- Department : Cyber Security
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 11
-- DEPARTMENT: DATA SCIENCE
-- PURPOSE: Create User Accounts for Data Science Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- DATA SCIENCE - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'farhan.ahmad',
'farhan.ahmad@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sana.javed',
'sana.javed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'waqas.ali',
'waqas.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'mahnoor.saeed',
'mahnoor.saeed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hamza.khan',
'hamza.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 11 SUMMARY
-- ===========================================================
-- Department : Data Science
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 12)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 12
-- DEPARTMENT: DATA SCIENCE
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- DATA SCIENCE TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'farhan.ahmad'),
    (SELECT department_id FROM Departments WHERE department_code = 'DS'),
    'UOH-DS-001',
    'Farhan',
    'Ahmad',
    'Male',
    '1981-04-18',
    '03001239001',
    'farhan.ahmad@uoh.edu.pk',
    'Professor',
    'PhD Data Science',
    'Machine Learning',
    '2011-09-05',
    'IB-401',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'sana.javed'),
    (SELECT department_id FROM Departments WHERE department_code = 'DS'),
    'UOH-DS-002',
    'Sana',
    'Javed',
    'Female',
    '1987-11-22',
    '03001239002',
    'sana.javed@uoh.edu.pk',
    'Associate Professor',
    'PhD Artificial Intelligence',
    'Deep Learning',
    '2015-08-17',
    'IB-402',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'waqas.ali'),
    (SELECT department_id FROM Departments WHERE department_code = 'DS'),
    'UOH-DS-003',
    'Waqas',
    'Ali',
    'Male',
    '1990-02-09',
    '03001239003',
    'waqas.ali@uoh.edu.pk',
    'Assistant Professor',
    'MS Data Science',
    'Big Data Analytics',
    '2019-09-02',
    'IB-403',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'mahnoor.saeed'),
    (SELECT department_id FROM Departments WHERE department_code = 'DS'),
    'UOH-DS-004',
    'Mahnoor',
    'Saeed',
    'Female',
    '1993-06-15',
    '03001239004',
    'mahnoor.saeed@uoh.edu.pk',
    'Lecturer',
    'MS Data Science',
    'Data Visualization',
    '2022-01-10',
    'IB-404',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'hamza.khan'),
    (SELECT department_id FROM Departments WHERE department_code = 'DS'),
    'UOH-DS-005',
    'Hamza',
    'Khan',
    'Male',
    '1994-12-01',
    '03001239005',
    'hamza.khan@uoh.edu.pk',
    'Lecturer',
    'MS Artificial Intelligence',
    'Business Intelligence',
    '2023-02-13',
    'IB-405',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 12 SUMMARY
-- ===========================================================
-- Department : Data Science
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 13
-- DEPARTMENT: CIVIL ENGINEERING
-- PURPOSE: Create User Accounts for Civil Engineering Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CIVIL ENGINEERING - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'ahmed.rehman',
'ahmed.rehman@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'aisha.nawaz',
'aisha.nawaz@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'bilal.aslam',
'bilal.aslam@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sana.riaz',
'sana.riaz@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'umer.farooq',
'umer.farooq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 13 SUMMARY
-- ===========================================================
-- Department : Civil Engineering
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 14)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 14
-- DEPARTMENT: CIVIL ENGINEERING
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CIVIL ENGINEERING TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'ahmed.rehman'),
    (SELECT department_id FROM Departments WHERE department_code = 'CE'),
    'UOH-CE-001',
    'Ahmed',
    'Rehman',
    'Male',
    '1980-03-12',
    '03001339001',
    'ahmed.rehman@uoh.edu.pk',
    'Professor',
    'PhD Civil Engineering',
    'Structural Engineering',
    '2010-09-01',
    'ENG-101',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'aisha.nawaz'),
    (SELECT department_id FROM Departments WHERE department_code = 'CE'),
    'UOH-CE-002',
    'Aisha',
    'Nawaz',
    'Female',
    '1986-08-19',
    '03001339002',
    'aisha.nawaz@uoh.edu.pk',
    'Associate Professor',
    'PhD Civil Engineering',
    'Transportation Engineering',
    '2014-08-18',
    'ENG-102',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'bilal.aslam'),
    (SELECT department_id FROM Departments WHERE department_code = 'CE'),
    'UOH-CE-003',
    'Bilal',
    'Aslam',
    'Male',
    '1989-11-07',
    '03001339003',
    'bilal.aslam@uoh.edu.pk',
    'Assistant Professor',
    'MS Civil Engineering',
    'Geotechnical Engineering',
    '2018-09-03',
    'ENG-103',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'sana.riaz'),
    (SELECT department_id FROM Departments WHERE department_code = 'CE'),
    'UOH-CE-004',
    'Sana',
    'Riaz',
    'Female',
    '1992-02-25',
    '03001339004',
    'sana.riaz@uoh.edu.pk',
    'Lecturer',
    'MS Civil Engineering',
    'Construction Management',
    '2021-01-11',
    'ENG-104',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'umer.farooq'),
    (SELECT department_id FROM Departments WHERE department_code = 'CE'),
    'UOH-CE-005',
    'Umer',
    'Farooq',
    'Male',
    '1993-09-14',
    '03001339005',
    'umer.farooq@uoh.edu.pk',
    'Lecturer',
    'MS Civil Engineering',
    'Environmental Engineering',
    '2023-02-06',
    'ENG-105',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 14 SUMMARY
-- ===========================================================
-- Department : Civil Engineering
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 15
-- DEPARTMENT: ELECTRICAL ENGINEERING
-- PURPOSE: Create User Accounts for Electrical Engineering Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ELECTRICAL ENGINEERING - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'kamran.ahmed',
'kamran.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sadia.ashraf',
'sadia.ashraf@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'zeeshan.ali',
'zeeshan.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'iqra.shah',
'iqra.shah@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hamid.rafiq',
'hamid.rafiq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 15 SUMMARY
-- ===========================================================
-- Department : Electrical Engineering
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 16)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 16
-- DEPARTMENT: ELECTRICAL ENGINEERING
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ELECTRICAL ENGINEERING TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'kamran.ahmed'),
    (SELECT department_id FROM Departments WHERE department_code = 'EE'),
    'UOH-EE-001',
    'Kamran',
    'Ahmed',
    'Male',
    '1981-04-18',
    '03001449001',
    'kamran.ahmed@uoh.edu.pk',
    'Professor',
    'PhD Electrical Engineering',
    'Power Systems',
    '2009-09-07',
    'ENG-201',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'sadia.ashraf'),
    (SELECT department_id FROM Departments WHERE department_code = 'EE'),
    'UOH-EE-002',
    'Sadia',
    'Ashraf',
    'Female',
    '1985-09-21',
    '03001449002',
    'sadia.ashraf@uoh.edu.pk',
    'Associate Professor',
    'PhD Electrical Engineering',
    'Control Systems',
    '2013-08-19',
    'ENG-202',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'zeeshan.ali'),
    (SELECT department_id FROM Departments WHERE department_code = 'EE'),
    'UOH-EE-003',
    'Zeeshan',
    'Ali',
    'Male',
    '1989-02-14',
    '03001449003',
    'zeeshan.ali@uoh.edu.pk',
    'Assistant Professor',
    'MS Electrical Engineering',
    'Electronics',
    '2018-02-12',
    'ENG-203',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'iqra.shah'),
    (SELECT department_id FROM Departments WHERE department_code = 'EE'),
    'UOH-EE-004',
    'Iqra',
    'Shah',
    'Female',
    '1992-11-08',
    '03001449004',
    'iqra.shah@uoh.edu.pk',
    'Lecturer',
    'MS Electrical Engineering',
    'Communication Systems',
    '2021-09-06',
    'ENG-204',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'hamid.rafiq'),
    (SELECT department_id FROM Departments WHERE department_code = 'EE'),
    'UOH-EE-005',
    'Hamid',
    'Rafiq',
    'Male',
    '1994-01-27',
    '03001449005',
    'hamid.rafiq@uoh.edu.pk',
    'Lecturer',
    'MS Electrical Engineering',
    'Embedded Systems',
    '2023-01-30',
    'ENG-205',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 16 SUMMARY
-- ===========================================================
-- Department : Electrical Engineering
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 17
-- DEPARTMENT: MECHANICAL ENGINEERING
-- PURPOSE: Create User Accounts for Mechanical Engineering Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- MECHANICAL ENGINEERING - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'waqar.ahmed',
'waqar.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hina.aslam',
'hina.aslam@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'farhan.iqbal',
'farhan.iqbal@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sana.abid',
'sana.abid@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'adeel.khan',
'adeel.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 17 SUMMARY
-- ===========================================================
-- Department : Mechanical Engineering
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 18)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 18
-- DEPARTMENT: MECHANICAL ENGINEERING
-- PURPOSE: Create Teacher Profiles
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- MECHANICAL ENGINEERING TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
    (SELECT user_id FROM Users WHERE username = 'waqar.ahmed'),
    (SELECT department_id FROM Departments WHERE department_code = 'ME'),
    'UOH-ME-001',
    'Waqar',
    'Ahmed',
    'Male',
    '1980-06-12',
    '03001559001',
    'waqar.ahmed@uoh.edu.pk',
    'Professor',
    'PhD Mechanical Engineering',
    'Thermal Engineering',
    '2008-09-08',
    'ENG-301',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'hina.aslam'),
    (SELECT department_id FROM Departments WHERE department_code = 'ME'),
    'UOH-ME-002',
    'Hina',
    'Aslam',
    'Female',
    '1986-03-19',
    '03001559002',
    'hina.aslam@uoh.edu.pk',
    'Associate Professor',
    'PhD Mechanical Engineering',
    'Manufacturing Engineering',
    '2012-08-20',
    'ENG-302',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'farhan.iqbal'),
    (SELECT department_id FROM Departments WHERE department_code = 'ME'),
    'UOH-ME-003',
    'Farhan',
    'Iqbal',
    'Male',
    '1989-09-07',
    '03001559003',
    'farhan.iqbal@uoh.edu.pk',
    'Assistant Professor',
    'MS Mechanical Engineering',
    'Robotics',
    '2018-02-05',
    'ENG-303',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'sana.abid'),
    (SELECT department_id FROM Departments WHERE department_code = 'ME'),
    'UOH-ME-004',
    'Sana',
    'Abid',
    'Female',
    '1992-12-15',
    '03001559004',
    'sana.abid@uoh.edu.pk',
    'Lecturer',
    'MS Mechanical Engineering',
    'CAD/CAM',
    '2021-09-13',
    'ENG-304',
    'Permanent',
    'Active'
),

(
    (SELECT user_id FROM Users WHERE username = 'adeel.khan'),
    (SELECT department_id FROM Departments WHERE department_code = 'ME'),
    'UOH-ME-005',
    'Adeel',
    'Khan',
    'Male',
    '1994-04-28',
    '03001559005',
    'adeel.khan@uoh.edu.pk',
    'Lecturer',
    'MS Mechanical Engineering',
    'Industrial Engineering',
    '2023-01-23',
    'ENG-305',
    'Permanent',
    'Active'
);

-- ===========================================================
-- PART 18 SUMMARY
-- ===========================================================
-- Department : Mechanical Engineering
-- Teacher Profiles Created : 5
-- Department Completed : YES
-- HOD Assignment : Pending (Final Stage)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 19
-- DEPARTMENT: BUSINESS ADMINISTRATION
-- PURPOSE: Create User Accounts for Business Administration Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- BUSINESS ADMINISTRATION - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'usman.malik',
'usman.malik@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'ayesha.nawaz',
'ayesha.nawaz@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'kamran.ali',
'kamran.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'maria.siddiqui',
'maria.siddiqui@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hamza.ali',
'hamza.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 19 SUMMARY
-- ===========================================================
-- Department : Business Administration
-- User Accounts Created : 5
-- Teachers Table : Pending (Part 20)
-- HOD Assignment : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 20
-- DEPARTMENT: BUSINESS ADMINISTRATION
-- PURPOSE: Create Business Administration Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- BUSINESS ADMINISTRATION - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='usman.malik'),
(SELECT department_id FROM Departments WHERE department_code='BBA'),
'UOH-BBA-001',
'Usman',
'Malik',
'Male',
'1980-03-15',
'+92-300-4100001',
'usman.malik@uoh.edu.pk',
'Professor',
'PhD Business Administration',
'Strategic Management',
'2013-09-01',
'Management Block - Room 201',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='ayesha.nawaz'),
(SELECT department_id FROM Departments WHERE department_code='BBA'),
'UOH-BBA-002',
'Ayesha',
'Nawaz',
'Female',
'1985-07-22',
'+92-300-4100002',
'ayesha.nawaz@uoh.edu.pk',
'Associate Professor',
'PhD Human Resource Management',
'Human Resource Management',
'2015-08-10',
'Management Block - Room 202',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='kamran.ali'),
(SELECT department_id FROM Departments WHERE department_code='BBA'),
'UOH-BBA-003',
'Kamran',
'Ali',
'Male',
'1988-01-18',
'+92-300-4100003',
'kamran.ali@uoh.edu.pk',
'Assistant Professor',
'PhD Marketing',
'Marketing Management',
'2018-02-05',
'Management Block - Room 203',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='maria.siddiqui'),
(SELECT department_id FROM Departments WHERE department_code='BBA'),
'UOH-BBA-004',
'Maria',
'Siddiqui',
'Female',
'1990-09-11',
'+92-300-4100004',
'maria.siddiqui@uoh.edu.pk',
'Lecturer',
'MS Business Administration',
'Finance',
'2021-09-15',
'Management Block - Room 204',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='hamza.ali'),
(SELECT department_id FROM Departments WHERE department_code='BBA'),
'UOH-BBA-005',
'Hamza',
'Ali',
'Male',
'1992-06-30',
'+92-300-4100005',
'hamza.ali@uoh.edu.pk',
'Lecturer',
'MBA',
'Entrepreneurship',
'2023-01-20',
'Management Block - Room 205',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 20 SUMMARY
-- ===========================================================
-- Department        : Business Administration
-- Teachers Created  : 5
-- Employee IDs      : UOH-BBA-001 → UOH-BBA-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 21
-- DEPARTMENT: ECONOMICS
-- PURPOSE: Create User Accounts for Economics Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ECONOMICS - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'nida.khan',
'nida.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'faisal.rahman',
'faisal.rahman@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sadia.akhtar',
'sadia.akhtar@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'waqas.abbasi',
'waqas.abbasi@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'maryam.yousaf',
'maryam.yousaf@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 21 SUMMARY
-- ===========================================================
-- Department        : Economics
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 22)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 22
-- DEPARTMENT: ECONOMICS
-- PURPOSE: Create Economics Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ECONOMICS - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='nida.khan'),
(SELECT department_id FROM Departments WHERE department_code='ECO'),
'UOH-ECO-001',
'Nida',
'Khan',
'Female',
'1981-04-18',
'+92-300-4200001',
'nida.khan@uoh.edu.pk',
'Professor',
'PhD Economics',
'Development Economics',
'2012-09-01',
'Management Block - Room 301',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='faisal.rahman'),
(SELECT department_id FROM Departments WHERE department_code='ECO'),
'UOH-ECO-002',
'Faisal',
'Rahman',
'Male',
'1984-08-12',
'+92-300-4200002',
'faisal.rahman@uoh.edu.pk',
'Associate Professor',
'PhD Economics',
'Macroeconomics',
'2015-02-15',
'Management Block - Room 302',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='sadia.akhtar'),
(SELECT department_id FROM Departments WHERE department_code='ECO'),
'UOH-ECO-003',
'Sadia',
'Akhtar',
'Female',
'1988-02-25',
'+92-300-4200003',
'sadia.akhtar@uoh.edu.pk',
'Assistant Professor',
'PhD Economics',
'International Economics',
'2018-08-20',
'Management Block - Room 303',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='waqas.abbasi'),
(SELECT department_id FROM Departments WHERE department_code='ECO'),
'UOH-ECO-004',
'Waqas',
'Abbasi',
'Male',
'1990-10-05',
'+92-300-4200004',
'waqas.abbasi@uoh.edu.pk',
'Lecturer',
'MS Economics',
'Public Finance',
'2021-01-10',
'Management Block - Room 304',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='maryam.yousaf'),
(SELECT department_id FROM Departments WHERE department_code='ECO'),
'UOH-ECO-005',
'Maryam',
'Yousaf',
'Female',
'1992-06-14',
'+92-300-4200005',
'maryam.yousaf@uoh.edu.pk',
'Lecturer',
'MPhil Economics',
'Econometrics',
'2023-03-06',
'Management Block - Room 305',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 22 SUMMARY
-- ===========================================================
-- Department        : Economics
-- Teachers Created  : 5
-- Employee IDs      : UOH-ECO-001 → UOH-ECO-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 23
-- DEPARTMENT: COMMERCE
-- PURPOSE: Create User Accounts for Commerce Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- COMMERCE - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'farooq.ahmed',
'farooq.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'asma.rafique',
'asma.rafique@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'bilal.khan',
'bilal.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'iqra.ali',
'iqra.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'zeeshan.hussain',
'zeeshan.hussain@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 23 SUMMARY
-- ===========================================================
-- Department        : Commerce
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 24)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 24
-- DEPARTMENT: COMMERCE
-- PURPOSE: Create Commerce Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- COMMERCE - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='farooq.ahmed'),
(SELECT department_id FROM Departments WHERE department_code='COM'),
'UOH-COM-001',
'Farooq',
'Ahmed',
'Male',
'1980-02-14',
'+92-300-4300001',
'farooq.ahmed@uoh.edu.pk',
'Professor',
'PhD Commerce',
'Financial Accounting',
'2012-09-01',
'Management Block - Room 401',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='asma.rafique'),
(SELECT department_id FROM Departments WHERE department_code='COM'),
'UOH-COM-002',
'Asma',
'Rafique',
'Female',
'1984-11-09',
'+92-300-4300002',
'asma.rafique@uoh.edu.pk',
'Associate Professor',
'PhD Commerce',
'Corporate Finance',
'2015-08-15',
'Management Block - Room 402',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='bilal.khan'),
(SELECT department_id FROM Departments WHERE department_code='COM'),
'UOH-COM-003',
'Bilal',
'Khan',
'Male',
'1988-05-22',
'+92-300-4300003',
'bilal.khan@uoh.edu.pk',
'Assistant Professor',
'PhD Accounting',
'Auditing',
'2018-01-20',
'Management Block - Room 403',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='iqra.ali'),
(SELECT department_id FROM Departments WHERE department_code='COM'),
'UOH-COM-004',
'Iqra',
'Ali',
'Female',
'1991-07-18',
'+92-300-4300004',
'iqra.ali@uoh.edu.pk',
'Lecturer',
'MPhil Commerce',
'Taxation',
'2021-03-10',
'Management Block - Room 404',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='zeeshan.hussain'),
(SELECT department_id FROM Departments WHERE department_code='COM'),
'UOH-COM-005',
'Zeeshan',
'Hussain',
'Male',
'1993-01-30',
'+92-300-4300005',
'zeeshan.hussain@uoh.edu.pk',
'Lecturer',
'MS Accounting & Finance',
'Cost Accounting',
'2023-02-06',
'Management Block - Room 405',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 24 SUMMARY
-- ===========================================================
-- Department        : Commerce
-- Teachers Created  : 5
-- Employee IDs      : UOH-COM-001 → UOH-COM-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 25
-- DEPARTMENT: MATHEMATICS
-- PURPOSE: Create User Accounts for Mathematics Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- MATHEMATICS - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'hina.iqbal',
'hina.iqbal@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'ahmed.raza',
'ahmed.raza@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sana.ashraf',
'sana.ashraf@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'kamran.awan',
'kamran.awan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'noor.fatima',
'noor.fatima@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 25 SUMMARY
-- ===========================================================
-- Department        : Mathematics
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 26)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 26
-- DEPARTMENT: MATHEMATICS
-- PURPOSE: Create Mathematics Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- MATHEMATICS - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='hina.iqbal'),
(SELECT department_id FROM Departments WHERE department_code='MTH'),
'UOH-MTH-001',
'Hina',
'Iqbal',
'Female',
'1980-04-12',
'+92-300-4400001',
'hina.iqbal@uoh.edu.pk',
'Professor',
'PhD Mathematics',
'Applied Mathematics',
'2012-09-01',
'Science Block - Room 101',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='ahmed.raza'),
(SELECT department_id FROM Departments WHERE department_code='MTH'),
'UOH-MTH-002',
'Ahmed',
'Raza',
'Male',
'1984-08-25',
'+92-300-4400002',
'ahmed.raza@uoh.edu.pk',
'Associate Professor',
'PhD Mathematics',
'Pure Mathematics',
'2015-08-15',
'Science Block - Room 102',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='sana.ashraf'),
(SELECT department_id FROM Departments WHERE department_code='MTH'),
'UOH-MTH-003',
'Sana',
'Ashraf',
'Female',
'1988-03-18',
'+92-300-4400003',
'sana.ashraf@uoh.edu.pk',
'Assistant Professor',
'PhD Mathematics',
'Numerical Analysis',
'2018-01-22',
'Science Block - Room 103',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='kamran.awan'),
(SELECT department_id FROM Departments WHERE department_code='MTH'),
'UOH-MTH-004',
'Kamran',
'Awan',
'Male',
'1991-10-05',
'+92-300-4400004',
'kamran.awan@uoh.edu.pk',
'Lecturer',
'MPhil Mathematics',
'Statistics',
'2021-03-10',
'Science Block - Room 104',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='noor.fatima'),
(SELECT department_id FROM Departments WHERE department_code='MTH'),
'UOH-MTH-005',
'Noor',
'Fatima',
'Female',
'1993-06-30',
'+92-300-4400005',
'noor.fatima@uoh.edu.pk',
'Lecturer',
'MS Mathematics',
'Operations Research',
'2023-02-06',
'Science Block - Room 105',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 26 SUMMARY
-- ===========================================================
-- Department        : Mathematics
-- Teachers Created  : 5
-- Employee IDs      : UOH-MTH-001 → UOH-MTH-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 27
-- DEPARTMENT: PHYSICS
-- PURPOSE: Create User Accounts for Physics Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- PHYSICS - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'farhan.qureshi',
'farhan.qureshi@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'sadia.rafiq',
'sadia.rafiq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'usman.tariq',
'usman.tariq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'aiman.sheikh',
'aiman.sheikh@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'zubair.ahmad',
'zubair.ahmad@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 27 SUMMARY
-- ===========================================================
-- Department        : Physics
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 28)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 28
-- DEPARTMENT: PHYSICS
-- PURPOSE: Create Physics Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- PHYSICS - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='farhan.qureshi'),
(SELECT department_id FROM Departments WHERE department_code='PHY'),
'UOH-PHY-001',
'Farhan',
'Qureshi',
'Male',
'1980-03-16',
'+92-300-4500001',
'farhan.qureshi@uoh.edu.pk',
'Professor',
'PhD Physics',
'Quantum Physics',
'2012-09-01',
'Science Block - Room 201',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='sadia.rafiq'),
(SELECT department_id FROM Departments WHERE department_code='PHY'),
'UOH-PHY-002',
'Sadia',
'Rafiq',
'Female',
'1984-09-12',
'+92-300-4500002',
'sadia.rafiq@uoh.edu.pk',
'Associate Professor',
'PhD Physics',
'Solid State Physics',
'2015-08-15',
'Science Block - Room 202',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='usman.tariq'),
(SELECT department_id FROM Departments WHERE department_code='PHY'),
'UOH-PHY-003',
'Usman',
'Tariq',
'Male',
'1988-01-28',
'+92-300-4500003',
'usman.tariq@uoh.edu.pk',
'Assistant Professor',
'PhD Physics',
'Nuclear Physics',
'2018-02-05',
'Science Block - Room 203',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='aiman.sheikh'),
(SELECT department_id FROM Departments WHERE department_code='PHY'),
'UOH-PHY-004',
'Aiman',
'Sheikh',
'Female',
'1991-06-21',
'+92-300-4500004',
'aiman.sheikh@uoh.edu.pk',
'Lecturer',
'MPhil Physics',
'Electromagnetism',
'2021-03-10',
'Science Block - Room 204',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='zubair.ahmad'),
(SELECT department_id FROM Departments WHERE department_code='PHY'),
'UOH-PHY-005',
'Zubair',
'Ahmad',
'Male',
'1993-11-09',
'+92-300-4500005',
'zubair.ahmad@uoh.edu.pk',
'Lecturer',
'MS Physics',
'Applied Physics',
'2023-02-06',
'Science Block - Room 205',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 28 SUMMARY
-- ===========================================================
-- Department        : Physics
-- Teachers Created  : 5
-- Employee IDs      : UOH-PHY-001 → UOH-PHY-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 29
-- DEPARTMENT: CHEMISTRY
-- PURPOSE: Create User Accounts for Chemistry Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CHEMISTRY - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'khalid.mahmood',
'khalid.mahmood@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'samira.yasin',
'samira.yasin@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'adnan.waheed',
'adnan.waheed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hira.aslam',
'hira.aslam@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'faizan.abbas',
'faizan.abbas@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 29 SUMMARY
-- ===========================================================
-- Department        : Chemistry
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 30)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 30
-- DEPARTMENT: CHEMISTRY
-- PURPOSE: Create Chemistry Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- CHEMISTRY - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='khalid.mahmood'),
(SELECT department_id FROM Departments WHERE department_code='CHE'),
'UOH-CHE-001',
'Khalid',
'Mahmood',
'Male',
'1979-05-18',
'+92-300-4600001',
'khalid.mahmood@uoh.edu.pk',
'Professor',
'PhD Chemistry',
'Organic Chemistry',
'2011-09-01',
'Science Block - Room 301',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='samira.yasin'),
(SELECT department_id FROM Departments WHERE department_code='CHE'),
'UOH-CHE-002',
'Samira',
'Yasin',
'Female',
'1983-10-07',
'+92-300-4600002',
'samira.yasin@uoh.edu.pk',
'Associate Professor',
'PhD Chemistry',
'Analytical Chemistry',
'2014-08-15',
'Science Block - Room 302',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='adnan.waheed'),
(SELECT department_id FROM Departments WHERE department_code='CHE'),
'UOH-CHE-003',
'Adnan',
'Waheed',
'Male',
'1988-02-11',
'+92-300-4600003',
'adnan.waheed@uoh.edu.pk',
'Assistant Professor',
'PhD Chemistry',
'Physical Chemistry',
'2018-01-22',
'Science Block - Room 303',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='hira.aslam'),
(SELECT department_id FROM Departments WHERE department_code='CHE'),
'UOH-CHE-004',
'Hira',
'Aslam',
'Female',
'1991-07-26',
'+92-300-4600004',
'hira.aslam@uoh.edu.pk',
'Lecturer',
'MPhil Chemistry',
'Inorganic Chemistry',
'2021-03-10',
'Science Block - Room 304',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='faizan.abbas'),
(SELECT department_id FROM Departments WHERE department_code='CHE'),
'UOH-CHE-005',
'Faizan',
'Abbas',
'Male',
'1993-12-03',
'+92-300-4600005',
'faizan.abbas@uoh.edu.pk',
'Lecturer',
'MS Chemistry',
'Biochemistry',
'2023-02-06',
'Science Block - Room 305',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 30 SUMMARY
-- ===========================================================
-- Department        : Chemistry
-- Teachers Created  : 5
-- Employee IDs      : UOH-CHE-001 → UOH-CHE-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 31
-- DEPARTMENT: ENGLISH
-- PURPOSE: Create User Accounts for English Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ENGLISH - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'rashid.hassan',
'rashid.hassan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'ayesha.javed',
'ayesha.javed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'usman.qadir',
'usman.qadir@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'mahnoor.ali',
'mahnoor.ali@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'imran.khalid',
'imran.khalid@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 31 SUMMARY
-- ===========================================================
-- Department        : English
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 32)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 32
-- DEPARTMENT: ENGLISH
-- PURPOSE: Create English Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ENGLISH - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='rashid.hassan'),
(SELECT department_id FROM Departments WHERE department_code='ENG'),
'UOH-ENG-001',
'Rashid',
'Hassan',
'Male',
'1979-08-15',
'+92-300-4700001',
'rashid.hassan@uoh.edu.pk',
'Professor',
'PhD English Literature',
'English Literature',
'2011-09-01',
'Humanities Block - Room 101',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='ayesha.javed'),
(SELECT department_id FROM Departments WHERE department_code='ENG'),
'UOH-ENG-002',
'Ayesha',
'Javed',
'Female',
'1983-11-22',
'+92-300-4700002',
'ayesha.javed@uoh.edu.pk',
'Associate Professor',
'PhD Applied Linguistics',
'Applied Linguistics',
'2014-08-15',
'Humanities Block - Room 102',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='usman.qadir'),
(SELECT department_id FROM Departments WHERE department_code='ENG'),
'UOH-ENG-003',
'Usman',
'Qadir',
'Male',
'1988-03-18',
'+92-300-4700003',
'usman.qadir@uoh.edu.pk',
'Assistant Professor',
'PhD English Literature',
'Modern Poetry',
'2018-01-22',
'Humanities Block - Room 103',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='mahnoor.ali'),
(SELECT department_id FROM Departments WHERE department_code='ENG'),
'UOH-ENG-004',
'Mahnoor',
'Ali',
'Female',
'1991-06-09',
'+92-300-4700004',
'mahnoor.ali@uoh.edu.pk',
'Lecturer',
'MPhil English',
'Communication Skills',
'2021-03-10',
'Humanities Block - Room 104',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='imran.khalid'),
(SELECT department_id FROM Departments WHERE department_code='ENG'),
'UOH-ENG-005',
'Imran',
'Khalid',
'Male',
'1993-10-27',
'+92-300-4700005',
'imran.khalid@uoh.edu.pk',
'Lecturer',
'MS English',
'Academic Writing',
'2023-02-06',
'Humanities Block - Room 105',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 32 SUMMARY
-- ===========================================================
-- Department        : English
-- Teachers Created  : 5
-- Employee IDs      : UOH-ENG-001 → UOH-ENG-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 33
-- DEPARTMENT: PSYCHOLOGY
-- PURPOSE: Create User Accounts for Psychology Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- PSYCHOLOGY - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'saba.naz',
'saba.naz@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'atif.rehman',
'atif.rehman@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'komal.ashraf',
'komal.ashraf@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'waheed.akram',
'waheed.akram@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'mehwish.khalid',
'mehwish.khalid@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 33 SUMMARY
-- ===========================================================
-- Department        : Psychology
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 34)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 34
-- DEPARTMENT: PSYCHOLOGY
-- PURPOSE: Create Psychology Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- PSYCHOLOGY - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='saba.naz'),
(SELECT department_id FROM Departments WHERE department_code='PSY'),
'UOH-PSY-001',
'Saba',
'Naz',
'Female',
'1981-03-12',
'+92-300-4800001',
'saba.naz@uoh.edu.pk',
'Professor',
'PhD Psychology',
'Clinical Psychology',
'2012-09-01',
'Humanities Block - Room 201',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='atif.rehman'),
(SELECT department_id FROM Departments WHERE department_code='PSY'),
'UOH-PSY-002',
'Atif',
'Rehman',
'Male',
'1984-09-18',
'+92-300-4800002',
'atif.rehman@uoh.edu.pk',
'Associate Professor',
'PhD Psychology',
'Cognitive Psychology',
'2015-08-15',
'Humanities Block - Room 202',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='komal.ashraf'),
(SELECT department_id FROM Departments WHERE department_code='PSY'),
'UOH-PSY-003',
'Komal',
'Ashraf',
'Female',
'1988-01-26',
'+92-300-4800003',
'komal.ashraf@uoh.edu.pk',
'Assistant Professor',
'PhD Psychology',
'Educational Psychology',
'2018-01-22',
'Humanities Block - Room 203',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='waheed.akram'),
(SELECT department_id FROM Departments WHERE department_code='PSY'),
'UOH-PSY-004',
'Waheed',
'Akram',
'Male',
'1991-07-09',
'+92-300-4800004',
'waheed.akram@uoh.edu.pk',
'Lecturer',
'MPhil Psychology',
'Counseling Psychology',
'2021-03-10',
'Humanities Block - Room 204',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='mehwish.khalid'),
(SELECT department_id FROM Departments WHERE department_code='PSY'),
'UOH-PSY-005',
'Mehwish',
'Khalid',
'Female',
'1993-11-15',
'+92-300-4800005',
'mehwish.khalid@uoh.edu.pk',
'Lecturer',
'MS Psychology',
'Behavioral Psychology',
'2023-02-06',
'Humanities Block - Room 205',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 34 SUMMARY
-- ===========================================================
-- Department        : Psychology
-- Teachers Created  : 5
-- Employee IDs      : UOH-PSY-001 → UOH-PSY-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 35
-- DEPARTMENT: EDUCATION
-- PURPOSE: Create User Accounts for Education Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- EDUCATION - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'nadia.ahmed',
'nadia.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'shahid.iqbal',
'shahid.iqbal@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'kiran.noor',
'kiran.noor@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'tariq.mahmood',
'tariq.mahmood@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'aiman.javed',
'aiman.javed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 36 SUMMARY
-- ===========================================================
-- Department        : Education
-- Teachers Created  : 5
-- Employee IDs      : UOH-EDU-001 → UOH-EDU-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 36
-- DEPARTMENT: EDUCATION
-- PURPOSE: Create Education Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- EDUCATION - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='nadia.ahmed'),
(SELECT department_id FROM Departments WHERE department_code='EDU'),
'UOH-EDU-001',
'Nadia',
'Ahmed',
'Female',
'1980-05-14',
'+92-300-4900001',
'nadia.ahmed@uoh.edu.pk',
'Professor',
'PhD Education',
'Higher Education',
'2012-09-01',
'Humanities Block - Room 301',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='shahid.iqbal'),
(SELECT department_id FROM Departments WHERE department_code='EDU'),
'UOH-EDU-002',
'Shahid',
'Iqbal',
'Male',
'1983-10-18',
'+92-300-4900002',
'shahid.iqbal@uoh.edu.pk',
'Associate Professor',
'PhD Education',
'Curriculum Development',
'2015-08-15',
'Humanities Block - Room 302',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='kiran.noor'),
(SELECT department_id FROM Departments WHERE department_code='EDU'),
'UOH-EDU-003',
'Kiran',
'Noor',
'Female',
'1988-02-21',
'+92-300-4900003',
'kiran.noor@uoh.edu.pk',
'Assistant Professor',
'PhD Education',
'Educational Leadership',
'2018-01-22',
'Humanities Block - Room 303',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='tariq.mahmood'),
(SELECT department_id FROM Departments WHERE department_code='EDU'),
'UOH-EDU-004',
'Tariq',
'Mahmood',
'Male',
'1991-07-09',
'+92-300-4900004',
'tariq.mahmood@uoh.edu.pk',
'Lecturer',
'MPhil Education',
'Teacher Education',
'2021-03-10',
'Humanities Block - Room 304',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='aiman.javed'),
(SELECT department_id FROM Departments WHERE department_code='EDU'),
'UOH-EDU-005',
'Aiman',
'Javed',
'Female',
'1993-12-01',
'+92-300-4900005',
'aiman.javed@uoh.edu.pk',
'Lecturer',
'MS Education',
'Educational Technology',
'2023-02-06',
'Humanities Block - Room 305',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 36 SUMMARY
-- ===========================================================
-- Department        : Education
-- Teachers Created  : 5
-- Employee IDs      : UOH-EDU-001 → UOH-EDU-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 37
-- DEPARTMENT: BIOTECHNOLOGY
-- PURPOSE: Create User Accounts for Biotechnology Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- BIOTECHNOLOGY - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'sara.khattak',
'sara.khattak@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'junaid.ahmed',
'junaid.ahmed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'momina.saeed',
'momina.saeed@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'hamza.nasir',
'hamza.nasir@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'iqra.farooq',
'iqra.farooq@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 37 SUMMARY
-- ===========================================================
-- Department        : Biotechnology
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 38)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 38
-- DEPARTMENT: BIOTECHNOLOGY
-- PURPOSE: Create Biotechnology Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- BIOTECHNOLOGY - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='sara.khattak'),
(SELECT department_id FROM Departments WHERE department_code='BIO'),
'UOH-BIO-001',
'Sara',
'Khattak',
'Female',
'1980-04-15',
'+92-300-5000001',
'sara.khattak@uoh.edu.pk',
'Professor',
'PhD Biotechnology',
'Molecular Biotechnology',
'2012-09-01',
'Life Sciences Block - Room 101',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='junaid.ahmed'),
(SELECT department_id FROM Departments WHERE department_code='BIO'),
'UOH-BIO-002',
'Junaid',
'Ahmed',
'Male',
'1984-08-20',
'+92-300-5000002',
'junaid.ahmed@uoh.edu.pk',
'Associate Professor',
'PhD Biotechnology',
'Genetic Engineering',
'2015-08-15',
'Life Sciences Block - Room 102',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='momina.saeed'),
(SELECT department_id FROM Departments WHERE department_code='BIO'),
'UOH-BIO-003',
'Momina',
'Saeed',
'Female',
'1988-02-18',
'+92-300-5000003',
'momina.saeed@uoh.edu.pk',
'Assistant Professor',
'PhD Biotechnology',
'Industrial Biotechnology',
'2018-01-22',
'Life Sciences Block - Room 103',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='hamza.nasir'),
(SELECT department_id FROM Departments WHERE department_code='BIO'),
'UOH-BIO-004',
'Hamza',
'Nasir',
'Male',
'1991-09-10',
'+92-300-5000004',
'hamza.nasir@uoh.edu.pk',
'Lecturer',
'MPhil Biotechnology',
'Microbiology',
'2021-03-10',
'Life Sciences Block - Room 104',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='iqra.farooq'),
(SELECT department_id FROM Departments WHERE department_code='BIO'),
'UOH-BIO-005',
'Iqra',
'Farooq',
'Female',
'1993-11-28',
'+92-300-5000005',
'iqra.farooq@uoh.edu.pk',
'Lecturer',
'MS Biotechnology',
'Bioinformatics',
'2023-02-06',
'Life Sciences Block - Room 105',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 38 SUMMARY
-- ===========================================================
-- Department        : Biotechnology
-- Teachers Created  : 5
-- Employee IDs      : UOH-BIO-001 → UOH-BIO-005
-- HOD Assignment    : Pending (Final Update)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 39
-- DEPARTMENT: ENVIRONMENTAL SCIENCES
-- PURPOSE: Create User Accounts for Environmental Sciences Faculty
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ENVIRONMENTAL SCIENCES - USER ACCOUNTS
-- ===========================================================

INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified
)
VALUES

(
'farah.siddiqui',
'farah.siddiqui@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'habib.akbar',
'habib.akbar@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'mariam.abbas',
'mariam.abbas@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'owais.akhtar',
'owais.akhtar@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
),

(
'laiba.khan',
'laiba.khan@uoh.edu.pk',
'UOH@2025',
'teacher',
1,
1
);

-- ===========================================================
-- PART 39 SUMMARY
-- ===========================================================
-- Department        : Environmental Sciences
-- User Accounts     : 5
-- Teachers Table    : Pending (Part 40)
-- HOD Assignment    : Pending
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 40
-- DEPARTMENT: ENVIRONMENTAL SCIENCES
-- PURPOSE: Create Environmental Sciences Faculty Records
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ENVIRONMENTAL SCIENCES - TEACHERS
-- ===========================================================

INSERT INTO Teachers
(
    user_id,
    department_id,
    employee_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    phone,
    office_email,
    designation,
    qualification,
    specialization,
    joining_date,
    office_room,
    employment_type,
    status
)
VALUES

(
(SELECT user_id FROM Users WHERE username='farah.siddiqui'),
(SELECT department_id FROM Departments WHERE department_code='ENV'),
'UOH-ENV-001',
'Farah',
'Siddiqui',
'Female',
'1980-03-14',
'+92-300-5100001',
'farah.siddiqui@uoh.edu.pk',
'Professor',
'PhD Environmental Sciences',
'Environmental Management',
'2012-09-01',
'Life Sciences Block - Room 201',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='habib.akbar'),
(SELECT department_id FROM Departments WHERE department_code='ENV'),
'UOH-ENV-002',
'Habib',
'Akbar',
'Male',
'1984-07-21',
'+92-300-5100002',
'habib.akbar@uoh.edu.pk',
'Associate Professor',
'PhD Environmental Sciences',
'Climate Change',
'2015-08-15',
'Life Sciences Block - Room 202',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='mariam.abbas'),
(SELECT department_id FROM Departments WHERE department_code='ENV'),
'UOH-ENV-003',
'Mariam',
'Abbas',
'Female',
'1988-01-19',
'+92-300-5100003',
'mariam.abbas@uoh.edu.pk',
'Assistant Professor',
'PhD Environmental Sciences',
'Water Resources',
'2018-01-22',
'Life Sciences Block - Room 203',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='owais.akhtar'),
(SELECT department_id FROM Departments WHERE department_code='ENV'),
'UOH-ENV-004',
'Owais',
'Akhtar',
'Male',
'1991-09-05',
'+92-300-5100004',
'owais.akhtar@uoh.edu.pk',
'Lecturer',
'MPhil Environmental Sciences',
'Environmental Chemistry',
'2021-03-10',
'Life Sciences Block - Room 204',
'Permanent',
'Active'
),

(
(SELECT user_id FROM Users WHERE username='laiba.khan'),
(SELECT department_id FROM Departments WHERE department_code='ENV'),
'UOH-ENV-005',
'Laiba',
'Khan',
'Female',
'1993-11-27',
'+92-300-5100005',
'laiba.khan@uoh.edu.pk',
'Lecturer',
'MS Environmental Sciences',
'Biodiversity Conservation',
'2023-02-06',
'Life Sciences Block - Room 205',
'Permanent',
'Active'
);

-- ===========================================================
-- PART 40 SUMMARY
-- ===========================================================
-- Department        : Environmental Sciences
-- Teachers Created  : 5
-- Employee IDs      : UOH-ENV-001 → UOH-ENV-005
-- HOD Assignment    : Pending (Final Step)
-- ===========================================================
-- ===========================================================
-- FILE: 03_teachers.sql
-- PART 41
-- PURPOSE: Assign Head of Departments (HOD)
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- ASSIGN HOD TO ALL DEPARTMENTS
-- ===========================================================

UPDATE Departments
SET hod_user_id =
(
    SELECT T.user_id
    FROM Teachers T
    WHERE T.department_id = Departments.department_id
      AND T.designation = 'Professor'
    LIMIT 1
);

-- ===========================================================
-- VERIFICATION QUERY
-- ===========================================================

SELECT
    D.department_code,
    D.department_name,
    U.username AS hod_username,
    T.first_name || ' ' || T.last_name AS hod_name,
    T.designation
FROM Departments D
LEFT JOIN Users U
    ON D.hod_user_id = U.user_id
LEFT JOIN Teachers T
    ON U.user_id = T.user_id
ORDER BY D.department_code;

-- ===========================================================
-- PART 41 SUMMARY
-- ===========================================================
-- Total Departments : 20
-- HOD Assigned      : 20
-- Method            : First Professor of Each Department
-- Status            : Completed
-- ===========================================================