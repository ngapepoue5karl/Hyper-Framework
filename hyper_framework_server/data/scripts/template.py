# === 1. Définition des entrées ===
__hyper_inputs__ = [
    {"key": "input_file", "label": "Fichier d'entrée (.csv)", "format": "csv"}
]

# === Définitions des différentes importations ===
import pandas as pd
import os

# =============================================================================
# FONCTIONS DE TRAITEMENT
# =============================================================================

def charger_fichier(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Erreur lors du chargement du fichier : {e}")
        return pd.DataFrame({'Message': ['Hello World']})

def traiter_donnees(df):
    resultat_df = pd.DataFrame({
        'Colonne 1': ['Hello World'],
        'Colonne 2': ['Bienvenue dans Hyper-Framework'],
        'Statut': ['OK']
    })
    return resultat_df

def calculer_statistiques(df):
    stats = {
        'Nombre de lignes': len(df),
        'Nombre de colonnes': len(df.columns),
        'Message': 'Hello World'
    }
    return stats

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def run(input_file_paths, output_dir_path):
    """

    Args:
        input_file_paths (dict): Dictionnaire contenant les chemins des fichiers d'entrée
        output_dir_path (str): Chemin du répertoire de sortie
    
    Returns:
        list: Liste de dictionnaires contenant les résultats à afficher
    """
    results = []
    
    try:
        # --- Étape 1 : Chargement des fichiers ---
        input_df = charger_fichier(input_file_paths.get('input_file'))
        
        # --- Étape 2 : Traitement des données ---
        resultat_df = traiter_donnees(input_df)
        
        # --- Étape 3 : Calcul des statistiques ---
        stats = calculer_statistiques(resultat_df)
        
        # --- Étape 4 : Sauvegarde optionnelle (Excel) ---
        output_file = os.path.join(output_dir_path, "rapport_hello_world.xlsx")
        resultat_df.to_excel(output_file, index=False)
        print(f"Rapport sauvegardé : {output_file}")
        
        # --- Étape 5 : Structuration du résultat pour l'affichage ---
        results.append({
            'title': "Hello World - Exemple de Template",
            'dataframe': resultat_df,
            'display_columns': [
                {'key': 'Colonne 1', 'label': 'Message Principal'},
                {'key': 'Colonne 2', 'label': 'Description'},
                {'key': 'Statut', 'label': 'État'}
            ],
            'summary_stats': stats
        })
        
    except Exception as e:
        print(f"Une erreur est survenue durant l'exécution : {e}")
        import traceback
        traceback.print_exc()
        raise e
    
    return results