"""
Script de migration pour ajouter la gestion de la périodicité dans analysis_runs.

Ce script transforme la colonne 'week_label' en 'period_label' et ajoute une colonne 'periodicity'.
Les données existantes sont conservées avec une périodicité par défaut de 'WEEK'.

Utilisation:
    python migrate_add_periodicity.py
"""

import sqlite3
import os
import sys

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hyper_framework_server.db')


def migrate_database():
    """Applique la migration pour ajouter la périodicité."""
    
    print("🔄 Début de la migration pour ajouter la périodicité...")
    
    # Connexion à la base de données
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table analysis_runs existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_runs'
        """)
        
        if not cursor.fetchone():
            print("  La table 'analysis_runs' n'existe pas encore. Aucune migration nécessaire.")
            return
        
        # Vérifier si la colonne 'periodicity' existe déjà
        cursor.execute("PRAGMA table_info(analysis_runs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'periodicity' in columns:
            print(" La migration a déjà été appliquée. La colonne 'periodicity' existe déjà.")
            return
        
        print(" Création de la nouvelle table avec périodicité...")
        
        # Créer une nouvelle table temporaire avec la nouvelle structure
        cursor.execute("""
            CREATE TABLE analysis_runs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                control_id INTEGER NOT NULL,
                control_name TEXT NOT NULL,
                periodicity TEXT NOT NULL DEFAULT 'WEEK',
                period_label TEXT NOT NULL,
                username TEXT NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                results_json TEXT NOT NULL,
                files_info TEXT,
                FOREIGN KEY (control_id) REFERENCES controls(id) ON DELETE CASCADE
            )
        """)
        
        print(" Migration des données existantes...")
        
        # Copier les données de l'ancienne table vers la nouvelle
        # On renomme 'week_label' en 'period_label' et on ajoute 'periodicity' = 'WEEK' par défaut
        cursor.execute("""
            INSERT INTO analysis_runs_new 
                (id, control_id, control_name, periodicity, period_label, username, executed_at, results_json, files_info)
            SELECT 
                id, control_id, control_name, 'WEEK' as periodicity, week_label as period_label, 
                username, executed_at, results_json, files_info
            FROM analysis_runs
        """)
        
        print("  Suppression de l'ancienne table...")
        
        # Supprimer l'ancienne table
        cursor.execute("DROP TABLE analysis_runs")
        
        print("  Renommage de la nouvelle table...")
        
        # Renommer la nouvelle table
        cursor.execute("ALTER TABLE analysis_runs_new RENAME TO analysis_runs")
        
        # Valider la transaction
        conn.commit()
        
        print(" Migration réussie ! La périodicité a été ajoutée à la table 'analysis_runs'.")
        print("   - Colonne 'week_label' renommée en 'period_label'")
        print("   - Colonne 'periodicity' ajoutée (défaut: 'WEEK')")
        print(f"   - {cursor.rowcount} enregistrements migrés")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f" Erreur lors de la migration : {e}")
        sys.exit(1)
    
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_database()
