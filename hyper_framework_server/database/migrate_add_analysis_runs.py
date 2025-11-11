"""
Script de migration pour ajouter la table analysis_runs à une base de données existante.
Ce script doit être exécuté une seule fois pour ajouter la nouvelle table.
"""

import sqlite3
import os

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hyper_framework_server.db')

def migrate():
    """Ajoute la table analysis_runs si elle n'existe pas déjà"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la table existe déjà
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='analysis_runs'
    """)
    
    if cursor.fetchone():
        print("✓ La table 'analysis_runs' existe déjà. Migration non nécessaire.")
        conn.close()
        return
    
    # Créer la table
    print("Création de la table 'analysis_runs'...")
    cursor.execute("""
        CREATE TABLE analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            control_id INTEGER NOT NULL,
            control_name TEXT NOT NULL,
            week_label TEXT NOT NULL,
            username TEXT NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            results_json TEXT NOT NULL,
            files_info TEXT,
            FOREIGN KEY (control_id) REFERENCES controls(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Migration réussie ! La table 'analysis_runs' a été créée.")

if __name__ == '__main__':
    migrate()
