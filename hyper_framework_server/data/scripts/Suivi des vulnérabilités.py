# Métadonnées HyperFramework
__hyper_inputs__ = [
    {"key": "vulnerability_month_1", "label": "Vulnerability Findings - Mois Précédent (.csv)"},
    {"key": "vulnerability_month_2", "label": "Vulnerability Findings - Mois Actuel (.csv)"},
    {"key": "ad_workstations", "label": "AD Workstations (.csv) - optionnel"},
    {"key": "ad_servers", "label": "AD Servers (.csv) - optionnel"}
]

# Périodicité du contrôle (analyse mensuelle)
__hyper_periodicity__ = 'MONTH'

# Métadonnées du contrôle pour l'en-tête du rapport
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_02_VULN",
    "application": "Tanium",
    "layer": "Système",
    "risk_reference": "R082",
    "risk_name": "Dommage causés par un Hacker",
    "control_name": "Analyse des vulnérabilités sur le SI",
    "ref_description": "CTL_SSI_SYS_VUL_4",
    "description": "Répertorier les vulnérabilités sur le Système d’Information et assurer leur traitement.",
    "analyse": """•	Extraction des vulnérabilités à partir de la plateforme Tanium
•	Sélection des vulnérabilités
•	Regroupement par système/composant applicatif et par actif."""
}

# Pas de graphiques pour ce contrôle
__hyper_charts__ = []

import pandas as pd
import os
import json
from datetime import datetime


def read_csv_safely(path: str, sep=None) -> pd.DataFrame:
    """Lecture sécurisée d'un fichier CSV avec détection automatique du séparateur"""
    if sep is None:
        # Détection automatique du séparateur
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if ';' in first_line and first_line.count(';') > first_line.count(','):
                sep = ';'
            else:
                sep = ','
    
    try:
        df = pd.read_csv(path, sep=sep, engine='python', on_bad_lines='skip', encoding='utf-8')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture de {path}: {e}")
        raise


def load_ad_endpoints(ad_paths: list) -> set:
    """Charge les noms des endpoints depuis les fichiers AD"""
    ad_endpoints = set()
    
    for ad_path in ad_paths:
        if not ad_path or not os.path.exists(ad_path):
            continue
            
        try:
            # Lire en sautant la première ligne et avec délimiteur point-virgule
            df_ad = pd.read_csv(ad_path, sep=';', skiprows=1, encoding='utf-8')
            if 'Name' in df_ad.columns:
                # Ajouter les noms à l'ensemble (en majuscules pour comparaison insensible à la casse)
                names = df_ad['Name'].dropna().astype(str).str.strip().str.upper()
                ad_endpoints.update(names)
                print(f"  Fichier AD chargé: {len(names)} noms ajoutés")
        except Exception as e:
            print(f"  Erreur lors de la lecture de {ad_path}: {e}")
    
    print(f"\nTotal d'endpoints AD chargés: {len(ad_endpoints)}")
    return ad_endpoints


def process_vulnerability_files(vuln_mois_precedent: str, vuln_mois_actuel: str, ad_endpoints: set, output_dir: str):
    """
    Traite les fichiers de vulnérabilités et génère le rapport Excel.
    Compare le mois précédent avec le mois actuel.
    Retourne les statistiques de la comparaison.
    """
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'vulnerability_findings.xlsx')
    
    # Vérifier que les fichiers existent
    if not vuln_mois_precedent or vuln_mois_precedent.strip() == "":
        raise ValueError(" Le fichier du mois précédent n'a pas été chargé. Veuillez charger un fichier 'Vulnerability Findings - Mois Précédent'.")
    if not os.path.exists(vuln_mois_precedent):
        raise ValueError(f" Le fichier du mois précédent est introuvable: {vuln_mois_precedent}")
    
    if not vuln_mois_actuel or vuln_mois_actuel.strip() == "":
        raise ValueError(" Le fichier du mois actuel n'a pas été chargé. Veuillez charger un fichier 'Vulnerability Findings - Mois Actuel'.")
    if not os.path.exists(vuln_mois_actuel):
        raise ValueError(f" Le fichier du mois actuel est introuvable: {vuln_mois_actuel}")
    
    print(f"\n✓ Fichiers à traiter:")
    print(f"  - Mois précédent: {os.path.basename(vuln_mois_precedent)}")
    print(f"  - Mois actuel: {os.path.basename(vuln_mois_actuel)}")
    
    # === CHARGEMENT ET TRAITEMENT DES FICHIERS ===
    print("\n[1/3] Chargement et nettoyage des données...")
    
    # Charger le mois précédent
    df_precedent = read_csv_safely(vuln_mois_precedent)
    print(f"  Mois précédent: {len(df_precedent)} lignes")
    
    # Traiter la colonne 'Endpoint' : supprimer '.sabc.cm'
    if 'Endpoint' in df_precedent.columns:
        df_precedent['Endpoint'] = df_precedent['Endpoint'].str.replace('.sabc.cm', '', regex=False)
    
    # Ajouter la colonne 'concaténation' = Check ID + Endpoint
    if 'Check ID' in df_precedent.columns and 'Endpoint' in df_precedent.columns:
        df_precedent['concaténation'] = df_precedent['Check ID'].astype(str) + df_precedent['Endpoint'].astype(str)
    
    # Supprimer les doublons
    if 'concaténation' in df_precedent.columns:
        nb_avant = len(df_precedent)
        df_precedent = df_precedent.drop_duplicates(subset=['concaténation'])
        print(f"    Doublons supprimés: {nb_avant - len(df_precedent)}")
    
    # Charger le mois actuel
    df_actuel = read_csv_safely(vuln_mois_actuel)
    print(f"  Mois actuel: {len(df_actuel)} lignes")
    
    # Traiter la colonne 'Endpoint' : supprimer '.sabc.cm'
    if 'Endpoint' in df_actuel.columns:
        df_actuel['Endpoint'] = df_actuel['Endpoint'].str.replace('.sabc.cm', '', regex=False)
    
    # Ajouter la colonne 'concaténation'
    if 'Check ID' in df_actuel.columns and 'Endpoint' in df_actuel.columns:
        df_actuel['concaténation'] = df_actuel['Check ID'].astype(str) + df_actuel['Endpoint'].astype(str)
    
    # Supprimer les doublons
    if 'concaténation' in df_actuel.columns:
        nb_avant = len(df_actuel)
        df_actuel = df_actuel.drop_duplicates(subset=['concaténation'])
        print(f"    Doublons supprimés: {nb_avant - len(df_actuel)}")
        
    # === COMPARAISON ===
    print("\n[2/3] Comparaison des vulnérabilités...")
    
    # Utiliser la colonne 'concaténation' pour l'analyse
    keys_precedent = set(df_precedent['concaténation'])
    keys_actuel = set(df_actuel['concaténation'])

    # Vulnérabilités traitées : présentes dans le mois précédent mais PAS dans le mois actuel
    keys_traitees = keys_precedent - keys_actuel
    df_traitees = df_precedent[df_precedent['concaténation'].isin(keys_traitees)]

    # Vulnérabilités non traitées : présentes dans les DEUX mois
    keys_non_traitees = keys_precedent & keys_actuel
    df_non_traitees = df_actuel[df_actuel['concaténation'].isin(keys_non_traitees)]

    # Nouvelles vulnérabilités : présentes dans le mois actuel mais PAS dans le mois précédent
    keys_nouvelles = keys_actuel - keys_precedent
    df_nouvelles = df_actuel[df_actuel['concaténation'].isin(keys_nouvelles)]

    # Filtrer les vulnérabilités non traitées et nouvelles selon les endpoints AD
    if len(ad_endpoints) > 0 and 'Endpoint' in df_non_traitees.columns:
        nb_avant = len(df_non_traitees)
        df_non_traitees = df_non_traitees[df_non_traitees['Endpoint'].str.upper().isin(ad_endpoints)]
        nb_apres = len(df_non_traitees)
        if nb_avant > nb_apres:
            print(f"  Vulnérabilités non traitées filtrées (hors AD): {nb_avant - nb_apres} supprimées, {nb_apres} conservées")

    if len(ad_endpoints) > 0 and 'Endpoint' in df_nouvelles.columns:
        nb_avant = len(df_nouvelles)
        df_nouvelles = df_nouvelles[df_nouvelles['Endpoint'].str.upper().isin(ad_endpoints)]
        nb_apres = len(df_nouvelles)
        if nb_avant > nb_apres:
            print(f"  Nouvelles vulnérabilités filtrées (hors AD): {nb_avant - nb_apres} supprimées, {nb_apres} conservées")

    # Calcul du taux de contrôle
    nb_traitees = len(df_traitees)
    nb_precedent = len(df_precedent)
    nb_non_traitees = len(df_non_traitees)
    nb_nouvelles = len(df_nouvelles)
    
    if nb_precedent > 0:
        taux_controle = (nb_traitees / nb_precedent) * 100
    else:
        taux_controle = 0.0
    
    print(f"  Taux de contrôle : {taux_controle:.2f}%")
    print(f"  Vulnérabilités traitées : {nb_traitees}")
    print(f"  Vulnérabilités non traitées : {nb_non_traitees}")
    print(f"  Nouvelles vulnérabilités : {nb_nouvelles}")
    
    # === ÉCRITURE RAPIDE DU RAPPORT EXCEL (SANS TABLES FORMATÉES) ===
    print("\n[3/3] Génération rapide du rapport Excel...")
    
    # Utiliser openpyxl qui est plus rapide pour les gros fichiers
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        print("   Écriture des résultats d'analyse...")
        # Feuilles d'analyse (généralement plus petites)
        if len(df_traitees) > 0:
            df_traitees.to_excel(writer, sheet_name="Vulnérabilités_Traitées", index=False)
        
        if len(df_non_traitees) > 0:
            df_non_traitees.to_excel(writer, sheet_name="Vulnérabilités_Non_Traitées", index=False)
        
        if len(df_nouvelles) > 0:
            df_nouvelles.to_excel(writer, sheet_name="Nouvelles_Vulnérabilités", index=False)
        
        # Feuille récapitulative
        recap_data = {
            'Indicateur': ['Vulnérabilités du mois précédent', 'Vulnérabilités traitées', 
                          'Vulnérabilités non traitées', 'Nouvelles vulnérabilités', 
                          'Taux de contrôle (%)'],
            'Valeur': [nb_precedent, nb_traitees, nb_non_traitees, nb_nouvelles, round(taux_controle, 2)]
        }
        df_recap = pd.DataFrame(recap_data)
        df_recap.to_excel(writer, sheet_name='Récapitulatif', index=False)
        print("   Toutes les feuilles écrites avec succès")
    
    # Statistiques finales
    final_stats = {
        "taux_controle": round(taux_controle, 2),
        "vulnerabilites_traitees": nb_traitees,
        "vulnerabilites_non_traitees": nb_non_traitees,
        "nouvelles_vulnerabilites": nb_nouvelles
    }

    print("\n" + "="*60)
    print("Traitement terminé. Fichier Excel créé :", output_file)
    print("="*60)
    
    return final_stats, output_file


def run(input_file_paths: dict, output_dir_path: str): 
    """
    Point d'entrée HyperFramework
    
    Args:
        input_file_paths: Dictionnaire contenant les chemins des fichiers d'entrée
        output_dir_path: Chemin du dossier de sortie
    
    Returns:
        Liste contenant un dictionnaire avec les résultats
    """
    print("=" * 70)
    print("ANALYSE DES VULNÉRABILITÉS - DÉMARRAGE")
    print("=" * 70)
    
    # DÉBOGAGE COMPLET - Voir exactement ce qui est reçu
    print("\n DÉBOGAGE - Contenu de input_file_paths:")
    print(f"   Type: {type(input_file_paths)}")
    print(f"   Clés disponibles: {list(input_file_paths.keys())}")
    for key, value in input_file_paths.items():
        print(f"   - '{key}' = '{value}'")
    
    # Récupérer les fichiers d'entrée avec les bonnes clés
    vuln_mois_precedent = input_file_paths.get("vulnerability_month_1", "")
    vuln_mois_actuel = input_file_paths.get("vulnerability_month_2", "")
    ad_workstations = input_file_paths.get("ad_workstations", "")
    ad_servers = input_file_paths.get("ad_servers", "")
    
    # Message de débogage pour voir ce qui a été chargé
    print("\n Fichiers récupérés avec les clés:")
    print(f"  • vulnerability_month_1 (Mois précédent): {'✓ ' + vuln_mois_precedent if vuln_mois_precedent else '✗ NON TROUVÉ'}")
    print(f"  • vulnerability_month_2 (Mois actuel): {'✓ ' + vuln_mois_actuel if vuln_mois_actuel else '✗ NON TROUVÉ'}")
    print(f"  • ad_workstations: {'✓ ' + ad_workstations if ad_workstations else '✗ NON TROUVÉ'}")
    print(f"  • ad_servers: {'✓ ' + ad_servers if ad_servers else '✗ NON TROUVÉ'}")
    
    # Charger les endpoints AD (optionnel)
    print("\n[ÉTAPE 0] Chargement des endpoints AD...")
    ad_paths = [ad_workstations, ad_servers]
    ad_endpoints = load_ad_endpoints(ad_paths)
    
    # Traiter les fichiers de vulnérabilités
    final_stats, excel_path = process_vulnerability_files(
        vuln_mois_precedent, 
        vuln_mois_actuel, 
        ad_endpoints, 
        output_dir_path
    )
    
    # Préparer les résultats pour l'affichage dans l'application
    print("\n" + "=" * 70)
    print("✓ ANALYSE TERMINÉE AVEC SUCCÈS")
    print("=" * 70)
    
    return [{
        "title": "Suivi des vulnérabilités du SI",
        "excel_output": excel_path,
        "dataframe": None,  # Pas de tableau à afficher
        "display_columns": [],  # Pas de colonnes à afficher
        "summary_stats": {
            "Taux de contrôle": f"{final_stats['taux_controle']}%",
            "Vulnérabilités traitées": final_stats['vulnerabilites_traitees'],
            "Vulnérabilités non traitées": final_stats['vulnerabilites_non_traitees'],
            "Nouvelles vulnérabilités": final_stats['nouvelles_vulnerabilites']
        }
    }]