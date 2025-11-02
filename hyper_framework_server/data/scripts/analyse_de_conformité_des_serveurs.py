__hyper_inputs__ = [
    {"key": "ad_data", "label": "Extraction des serveurs AD (.csv)", "format": "csv"},
    {"key": "cs_data", "label": "Rapport de l'agent CrowdStrike (.csv)", "format": "csv"},
    {"key": "tn_data", "label": "Rapport de l'agent Tanium (.csv)", "format": "csv"},
    {"key": "externe_tanium", "label": "Fichier externe Tanium - Suivi (.xlsx)", "format": "xlsx"},
    {"key": "externe_crowdstrike", "label": "Fichier externe CrowdStrike - Suivi (.xlsx)", "format": "xlsx"},
]
# -------------------------------------------------------------------

import pandas as pd
import numpy as np
import re
import io
import os
import datetime

# --- Fonctions Utilitaires et d'Analyse ---

def clean_ad_data(file_path: str) -> pd.DataFrame:
    """Lit et nettoie un fichier AD brut depuis son chemin."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f: lines = f.readlines()
        if lines and lines[0].strip().startswith('#TYPE'): lines = lines[1:]
        cleaned_content = "".join([line.replace('"', '') for line in lines])
        return pd.read_csv(io.StringIO(cleaned_content), sep=';')
    except Exception as e:
        raise ValueError(f"Erreur lors du nettoyage du fichier AD {file_path}: {e}")

def load_and_prepare_external_file(file_path: str) -> pd.DataFrame:
    """Charge, nettoie et prépare un fichier de suivi externe (Excel) depuis la deuxième feuille."""
    if not file_path or not os.path.exists(file_path):
        return pd.DataFrame(columns=["Name_upper", "Observations"])
    
    try:
        # MODIFICATION : On ajoute sheet_name=1 pour lire la DEUXIÈME feuille
        df = pd.read_excel(file_path, sheet_name=1, engine='openpyxl')
        
    except IndexError:
        # Cette erreur se produit si le fichier a moins de 2 feuilles
        print(f"Avertissement: Impossible de trouver une deuxième feuille dans {file_path}. Le fichier sera ignoré.")
        return pd.DataFrame(columns=["Name_upper", "Observations"])
    except Exception as e:
        print(f"Avertissement: Erreur lors de la lecture du fichier Excel {file_path}. Erreur: {e}")
        return pd.DataFrame(columns=["Name_upper", "Observations"])

    if "Name" not in df.columns or "Observations" not in df.columns:
        print(f"Avertissement: Les colonnes 'Name' et/ou 'Observations' sont manquantes dans la deuxième feuille de {file_path}.")
        return pd.DataFrame(columns=["Name_upper", "Observations"])
        
    df = df[["Name", "Observations"]].copy()
    df.dropna(subset=['Name'], inplace=True)
    df = df.drop_duplicates(subset=['Name'], keep='first')
    df['Name_upper'] = df['Name'].astype(str).str.strip().str.lower()
    return df


def add_os_status(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute une colonne 'Status_OS' au DataFrame ('OK' si >= 2016, sinon 'NOK')."""
    if 'OperatingSystem' not in df.columns: raise ValueError("Le fichier AD doit contenir la colonne 'OperatingSystem'.")
    def is_compliant(os_str):
        if not isinstance(os_str, str) or "windows server" not in os_str.lower(): return False
        match = re.search(r'\b(20\d{2})\b', os_str)
        return match and int(match.group(1)) >= 2016
    df['Status_OS'] = np.where(df['OperatingSystem'].apply(is_compliant), 'OK', 'NOK')
    return df

def add_agent_status(ad_df: pd.DataFrame, agent_df: pd.DataFrame, agent_hostname_col: str, status_col_name: str) -> pd.DataFrame:
    """Ajoute une colonne de statut ('OK' si le serveur est trouvé, sinon 'NOK')."""
    if 'Name' not in ad_df.columns: raise ValueError("Colonne 'Name' manquante dans le fichier AD.")
    if agent_hostname_col not in agent_df.columns: raise ValueError(f"Colonne '{agent_hostname_col}' manquante dans le fichier de l'agent.")
    report_cols = ['description', 'LastLogonDate']
    for col in report_cols:
        if col not in ad_df.columns: ad_df[col] = 'N/A'
    ad_names_lower = ad_df['Name'].str.strip().str.lower()
    agent_hostnames_set = set(agent_df[agent_hostname_col].str.strip().str.lower())
    ad_df[status_col_name] = np.where(ad_names_lower.isin(agent_hostnames_set), 'OK', 'NOK')
    return ad_df

# --- POINT D'ENTRÉE DU SCRIPT ---

def run(input_file_paths, output_dir_path):
    results = []
    try:
        # --- 1. Chargement et nettoyage des données ---
        ad_df_base = clean_ad_data(input_file_paths.get('ad_data'))
        cs_df = pd.read_csv(input_file_paths.get('cs_data'))
        tn_df = pd.read_csv(input_file_paths.get('tn_data'))
        ext_cs_df = load_and_prepare_external_file(input_file_paths.get('externe_crowdstrike'))
        ext_tn_df = load_and_prepare_external_file(input_file_paths.get('externe_tanium'))
        
        if "Computer Name" in tn_df.columns:
            tn_df["Computer Name"] = tn_df["Computer Name"].str.replace(".sabc.cm", "", regex=False)
        else:
            raise ValueError("La colonne 'Computer Name' est manquante dans le rapport Tanium.")

        # --- 2. Enrichissement de base ---
        ad_df_enriched = add_os_status(ad_df_base.copy())
        ad_df_enriched = add_agent_status(ad_df_enriched, cs_df, "Hostname", "Status_CS")
        ad_df_enriched = add_agent_status(ad_df_enriched, tn_df, "Computer Name", "Status_TN")

        # --- 3. Intégration des suivis et calcul du résultat final ---
        ad_df_enriched['Name_upper'] = ad_df_enriched['Name'].astype(str).str.strip().str.lower()
        
        # Fusion pour CrowdStrike (utilise le DataFrame externe qui vient de la 2e feuille)
        cs_suivi_to_merge = ext_cs_df[['Name_upper', 'Observations']].rename(columns={'Observations': 'Suivi_CS'})
        ad_df_enriched = pd.merge(ad_df_enriched, cs_suivi_to_merge, on='Name_upper', how='left')
        
        pattern_cs_ok = 'Remonte sur Intune|CS installé'
        cond_suivi_ok_cs = ad_df_enriched['Suivi_CS'].str.contains(pattern_cs_ok, case=False, na=False)
        cond_base_ok_cs = (ad_df_enriched['Status_CS'] == 'OK')
        ad_df_enriched['Resultat_final_CS'] = np.where(cond_suivi_ok_cs | cond_base_ok_cs, 'OK', 'NOK')

        # Fusion pour Tanium (utilise le DataFrame externe qui vient de la 2e feuille)
        tn_suivi_to_merge = ext_tn_df[['Name_upper', 'Observations']].rename(columns={'Observations': 'Suivi_TN'})
        ad_df_enriched = pd.merge(ad_df_enriched, tn_suivi_to_merge, on='Name_upper', how='left')
        
        pattern_tn_ok = 'Remonte sur Intune|TN installé'
        cond_suivi_ok_tn = ad_df_enriched['Suivi_TN'].str.contains(pattern_tn_ok, case=False, na=False)
        cond_base_ok_tn = (ad_df_enriched['Status_TN'] == 'OK')
        ad_df_enriched['Resultat_final_TN'] = np.where(cond_suivi_ok_tn | cond_base_ok_tn, 'OK', 'NOK')
        
        ad_df_enriched.drop(columns=['Name_upper'], inplace=True)

        # Sauvegarde
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            output_filepath = os.path.join(output_dir_path, f"rapport_conformite_complet_{timestamp}.xlsx")
            ad_df_enriched.to_excel(output_filepath, index=False, engine='openpyxl')
        except Exception as e:
            print(f"Avertissement: Impossible de sauvegarder le rapport Excel complet: {e}")
        
        # --- 4. Construction des sections de résultat ---

        # Analyse 1: OS (inchangée)
        results.append({
            'title': "1. Conformité des OS Serveurs",
            # 'dataframe': ad_df_enriched[ad_df_enriched['Status_OS'] == 'NOK'],
            'dataframe': ad_df_enriched,
            'display_columns': [{'key': 'Name', 'label': "Nom du Serveur"}, {'key': 'OperatingSystem', 'label': "Système d'Exploitation"}, {'key': 'Status_OS', 'label': "Résultat"}],
            'summary_stats': {'Total serveurs analysés': len(ad_df_enriched), 'Serveurs non conformes': int((ad_df_enriched['Status_OS'] == 'NOK').sum()), 'Pourcentage de conformité': f"{(len(ad_df_enriched[ad_df_enriched['Status_OS'] == 'OK']) / len(ad_df_enriched)):.2%}" if len(ad_df_enriched) > 0 else "N/A"}
        })

        # Analyse 2: CrowdStrike (mise à jour)
        df_cs_nok = ad_df_enriched[ad_df_enriched['Resultat_final_CS'] == 'NOK']
        results.append({
            'title': "2. Couverture par l'agent CrowdStrike",
            # 'dataframe': df_cs_nok,
            'dataframe': ad_df_enriched,
            'display_columns': [
                {'key': 'Name', 'label': "Nom du Serveur"},
                {'key': 'Status_CS', 'label': "Conformité de base"},
                {'key': 'Suivi_CS', 'label': "Observations Suivi"},
                {'key': 'Resultat_final_CS', 'label': "Résultat Final"}
            ],
            'summary_stats': {'Total serveurs analysés': len(ad_df_enriched), 'Serveurs non couverts (final)': len(df_cs_nok), 'Pourcentage de couverture (final)': f"{(len(ad_df_enriched[ad_df_enriched['Resultat_final_CS'] == 'OK']) / len(ad_df_enriched)):.2%}" if len(ad_df_enriched) > 0 else "N/A"}
        })
            
        # Analyse 3: Tanium (mise à jour)
        df_tn_nok = ad_df_enriched[ad_df_enriched['Resultat_final_TN'] == 'NOK']
        results.append({
            'title': "3. Couverture par l'agent Tanium",
            # 'dataframe': df_tn_nok,
            'dataframe': ad_df_enriched,
            'display_columns': [
                {'key': 'Name', 'label': "Nom du Serveur"},
                {'key': 'Status_TN', 'label': "Conformité de base"},
                {'key': 'Suivi_TN', 'label': "Observations Suivi"},
                {'key': 'Resultat_final_TN', 'label': "Résultat Final"}
            ],
            'summary_stats': {'Total serveurs analysés': len(ad_df_enriched), 'Serveurs non couverts (final)': len(df_tn_nok), 'Pourcentage de couverture (final)': f"{(len(ad_df_enriched[ad_df_enriched['Resultat_final_TN'] == 'OK']) / len(ad_df_enriched)):.2%}" if len(ad_df_enriched) > 0 else "N/A"}
        })

    except Exception as e:
        print(f"ERREUR D'EXÉCUTION DU SCRIPT: {e}")
        import traceback
        traceback.print_exc()
        raise e
        
    return results