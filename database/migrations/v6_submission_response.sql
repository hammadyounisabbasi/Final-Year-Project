-- Safe additive support for text responses when file storage is unavailable.
ALTER TABLE Submissions ADD COLUMN response_text TEXT;
