#---> FICHIER MODIFIÉ : hyper_framework_server/database/database.py

import sqlite3
import click
from flask import current_app, g
import os
import sys

def _initialize_schema_if_needed(db):
    """
    Vérifie et crée les tables nécessaires sans détruire les données existantes.
    """
    cursor = db.cursor()
    
    # 1. Table 'users'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            is_temporary_password INTEGER DEFAULT 1
        );
    """)

    # 2. Table 'controls'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS controls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            input_definitions TEXT NOT NULL, 
            script_filename TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated_by TEXT
        );
    """)

    # La table ActionLogs n'est plus créée ici

    # 4. Vérifier si 'superadmin' doit être créé
    cursor.execute("SELECT id FROM users WHERE username = 'superadmin'")
    if not cursor.fetchone():
        click.echo("Superadmin not found. Creating initial superadmin...")
        db.execute("INSERT INTO users (username, password_hash, role, is_temporary_password) VALUES ('superadmin', 'placeholder', 'SUPER_ADMIN', 0)")
        from ..auth.auth_service import _update_superadmin_password_from_db_instance
        _update_superadmin_password_from_db_instance(db)
        click.echo("Superadmin initialized.")

    db.commit()

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DB_FILE']
        
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

        _initialize_schema_if_needed(g.db)
        
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_schema_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'hyper_framework_server', 'database', 'schema.sql')

def init_db_logic(db):
    schema_path = get_schema_path()
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()
    except FileNotFoundError:
        print(f"CRITICAL ERROR: schema.sql not found at path: {schema_path}")
        raise

@click.command('init-db')
def init_db_command():
    db = get_db()
    click.echo('Forcing re-initialization (destructive)...')
    init_db_logic(db)

    from ..auth.auth_service import _update_superadmin_password
    _update_superadmin_password()
    click.echo('Database re-initialized.')


def init_app(app):
    app.teardown_appcontext(close_db)