-- Safe additive fix: assignments must target a real enrollment section.
ALTER TABLE Assignments ADD COLUMN section TEXT;
