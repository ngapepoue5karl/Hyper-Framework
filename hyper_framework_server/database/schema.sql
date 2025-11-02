

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS controls;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_temporary_password INTEGER DEFAULT 1
);

INSERT INTO users (username, password_hash, role, is_temporary_password) VALUES ('superadmin', 'placeholder', 'SUPER_ADMIN', 0);


CREATE TABLE controls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    input_definitions TEXT NOT NULL, 
    script_filename TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_by TEXT 
);
