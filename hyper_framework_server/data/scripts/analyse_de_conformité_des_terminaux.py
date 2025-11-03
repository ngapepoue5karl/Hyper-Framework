# --- 1. Définition des entrées ---
__hyper_inputs__ = [
    {"key": "adws_file", "label": "Fichier ADWS - Export Active Directory", "format": "csv"},
    {"key": "glpi_file", "label": "Fichier GLPI - Inventaire", "format": "csv"},
    {"key": "intune_file", "label": "Fichier Intune - Devices", "format": "csv"},
    {"key": "tanium_file", "label": "Fichier Tanium - Agents", "format": "csv"},
    {"key": "crowdstrike_file", "label": "Fichier CrowdStrike", "format": "csv"},
    {"key": "laps_file", "label": "Fichier LAPS - Passwords", "format": "csv"},
    {"key": "externe_tanium", "label": "Fichier externe Tanium", "format": "xlsx"},
    {"key": "externe_crowdstrike", "label": "Fichier externe CrowdStrike", "format": "xlsx"},
    {"key": "externe_laps", "label": "Fichier externe LAPS ", "format": "xlsx"},
]

# --- Import des bibliothèques nécessaires ---
import pandas as pd
import numpy as np
import chardet
from io import StringIO
from datetime import datetime, timedelta
import re

# =============================================================================
# Fonctions de nettoyage et de préparation des données
# =============================================================================

def clean_adws_data(file_path):
    """Nettoie et charge le fichier d'export ADWS."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        encoding = chardet.detect(raw_data)['encoding']
    with open(file_path, 'r', encoding=encoding) as f:
        lignes = [ligne.strip() for ligne in f if ligne.strip()]
    lignes = lignes[1:]
    donnees = [ligne.replace('"', '').split(';') for ligne in lignes]
    df = pd.DataFrame(donnees[1:], columns=donnees[0])
    if 'OperatingSystem' in df.columns:
        valeurs_a_supprimer = ['linux', 'cisco', 'LTSB', 'LTSC', 'unknown']
        pattern = '|'.join(valeurs_a_supprimer)
        df = df[~df['OperatingSystem'].str.contains(pattern, case=False, na=False)]
    return df

def clean_tanium_data(file_path):
    """Nettoie et charge le fichier Tanium avec des lignes reconstruites."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        encoding = chardet.detect(raw_data)['encoding']
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        lignes = f.readlines()
    reconstruit = [lignes[0].strip()]
    buffer = ""
    for ligne in lignes[1:]:
        ligne = ligne.strip()
        if not ligne: continue
        buffer += " " + ligne
        if buffer.strip().endswith(",1"):
            reconstruit.append(buffer.strip())
            buffer = ""
    if buffer:
        reconstruit.append(buffer.strip())
    csv_reconstruit = "\n".join(reconstruit)
    df = pd.read_csv(StringIO(csv_reconstruit), sep=",", quotechar='"', engine="python")
    if 'Computer Name' in df.columns:
        df['Computer Name'] = df['Computer Name'].str.replace(r'\.sabc\.cm$', '', regex=True)
        df = df.rename(columns={"Computer Name": "Name"})
    return df

def load_generic_csv(file_path, sep=',', drop_last_cols=0):
    """Charge un fichier CSV standard."""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        encoding = chardet.detect(raw_data)['encoding']
    df = pd.read_csv(file_path, sep=sep, quotechar='"', encoding=encoding, low_memory=False)
    if drop_last_cols > 0:
        df = df.iloc[:, :-drop_last_cols]
    return df

def load_external_file(file_path):
    """Charge le fichier de suivi externe."""
    df = pd.read_excel(file_path)
    if "Observations" in df.columns and "Name" in df.columns:
        return df[["Name", "Observations"]]
    return pd.DataFrame(columns=["Name", "Observations"])

# =============================================================================
# Fonctions d'analyse
# =============================================================================

def get_os_compliance(series, min_build=19045):
    """Détermine si la version de l'OS est conforme."""
    builds = series.str.extract(r'\((\d+)\)').astype(float)
    return np.where(builds.iloc[:, 0] >= min_build, "OK", "NOK")

def get_os_compliance_win10_plus(series):
    """Détermine si l'OS est au moins Windows 10."""
    version_str = series.astype(str)
    return np.where(version_str.str.startswith("10.0") | version_str.str.startswith("11."), "OK", "NOK")

# --- 2. Fonction d'analyse principale ---
def run(input_file_paths, output_dir_path):
    """
    Fonction principale exécutée par le Hyper-Framework.
    """
    results = []

    try:
        # --- A. Chargement et nettoyage ---
        ad_df = clean_adws_data(input_file_paths.get('adws_file'))
        glpi_df = load_generic_csv(input_file_paths.get('glpi_file'), sep=';')
        intune_df = load_generic_csv(input_file_paths.get('intune_file'), drop_last_cols=2)
        tanium_df = clean_tanium_data(input_file_paths.get('tanium_file'))
        crowdstrike_df = load_generic_csv(input_file_paths.get('crowdstrike_file'))
        laps_df = load_generic_csv(input_file_paths.get('laps_file'))
        ext_tanium_df = load_external_file(input_file_paths.get('externe_tanium'))
        ext_crowdstrike_df = load_external_file(input_file_paths.get('externe_crowdstrike'))
        ext_laps_df = load_external_file(input_file_paths.get('externe_laps'))
        
        # --- B. Préparation de la base de données commune ---
        glpi_df.rename(columns={"Nom": "Name"}, inplace=True)
        glpi_subset = glpi_df[['Name', 'Lieu', 'Statut', 'Utilisateur']].drop_duplicates(subset=['Name'])

        lieu_dict = glpi_subset.set_index('Name')['Lieu'].to_dict()
        statut_dict = glpi_subset.set_index('Name')['Statut'].to_dict()
        utilisateur_dict = glpi_subset.set_index('Name')['Utilisateur'].to_dict()

        ad_df['Lieu'] = ad_df['Name'].map(lieu_dict)
        ad_df['Statut'] = ad_df['Name'].map(statut_dict)
        ad_df['Utilisateur'] = ad_df['Name'].map(utilisateur_dict)

        base_df = ad_df.copy()
        base_df['LastLogonDate'] = pd.to_datetime(base_df['LastLogonDate'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

        # --- C. Analyses ---

        # 1. Conformité des systèmes d'exploitation (pas de fusion ici)
        df1 = base_df.copy()
        df1['Résultat'] = get_os_compliance(df1['OperatingSystemVersion'])
        df1['LastLogonDate_short'] = df1['LastLogonDate'].dt.strftime('%Y-%m-%d')
        results.append({
            'title': "Conformité OS (Build >= 19045)",
            'dataframe': df1,
            'display_columns': [
                {'key': 'LastLogonDate_short', 'label': "Dernière Connexion"},
                {'key': 'Name', 'label': "Nom du Poste"},
                {'key': 'OperatingSystem', 'label': "OS"},
                {'key': 'OperatingSystemVersion', 'label': "Version OS"},
                {'key': 'Utilisateur', 'label': "Propriétaire GLPI"},
                {'key': 'Résultat', 'label': "Résultat Conformité"}
            ],
            'summary_stats': {
                'Total postes analysés': len(ad_df),
                'Postes non conformes (NOK)': len(df1[df1['Résultat'] == 'NOK']),
                'Taux de conformité': f"{(len(df1[df1['Résultat'] == 'OK'])/len(base_df.copy())*100):.2f}%"
            }
        })

        # 2. Conformité service Intune
        df2 = base_df.copy()
        intune_unique_df = intune_df.drop_duplicates(subset=['Device name'])
        
        # MISE À JOUR : Fusion insensible à la casse
        df2['Name_upper'] = df2['Name'].str.upper()
        intune_unique_df['Device name_upper'] = intune_unique_df['Device name'].str.upper()
        df2 = pd.merge(df2, intune_unique_df[['Device name', 'Compliance', 'Device name_upper']], left_on='Name_upper', right_on='Device name_upper', how='left')
        df2.drop(columns=['Name_upper'], inplace=True)
        
        df2['OS Conforme ?'] = get_os_compliance_win10_plus(df2['OperatingSystemVersion'])
        df2['Intune Déployé ?'] = np.where(df2['Device name'].notna(), df2['Name'], '#N/A')
        df2['Résultat'] = np.where((df2['Intune Déployé ?'] == '#N/A') | (df2['OS Conforme ?'] == 'NOK'), 'NOK', 'OK')
        conditions_intune = [
            (df2['Intune Déployé ?'] == '#N/A'),
            (df2['Résultat'] == 'OK') & (df2['Compliance'] == 'Compliant') & (df2['OperatingSystem'].str.contains('Windows', case=False, na=False))
        ]
        choix_intune = ['INTUNE NON DEPLOYE', 'OK']
        df2['Intune déployé et conforme'] = np.select(conditions_intune, choix_intune, default='NOK')
        df2['LastLogonDate_short'] = df2['LastLogonDate'].dt.strftime('%Y-%m-%d')
        results.append({
            'title': "Conformité du service Intune",
            'dataframe': df2,
            'display_columns': [
                {'key': 'LastLogonDate_short', 'label': "Dernière Connexion"},
                {'key': 'Name', 'label': "Nom du Poste"},
                {'key': 'OS Conforme ?', 'label': "OS Conforme ?"},
                {'key': 'Intune Déployé ?', 'label': "Intune Déployé ?"},
                {'key': 'Compliance', 'label': "Statut Conformité Intune"},
                {'key': 'Résultat', 'label': "Conformité de base"},
                {'key': 'Intune déployé et conforme', 'label': "Résultat Final"}
            ],
            'summary_stats': {
                'Nb total Postes ': len(base_df.copy()), 
                'Intune non Déployé ': len(df2[df2['Intune Déployé ?'] == '#N/A']),
                'Intune non Conforme': len(df2[df2['Intune déployé et conforme'] == 'NOK']),
                'Taux de déploiement': f"{(len(df2[df2['Intune Déployé ?'] != '#N/A'])/len(base_df.copy())*100):.2f}%",
                'Taux de conformité ': f"{(len(df2[df2['Intune déployé et conforme']== 'OK'])/len(df2[df2['Intune Déployé ?'] != '#N/A'])*100):.2f}%" if len(df2[df2['Intune Déployé ?'] != '#N/A']) > 0 else "0.00%"
            }
        })
        
        # 3. Conformité agent Tanium
        df3 = base_df.copy()
        tanium_unique_df = tanium_df.drop_duplicates(subset=['Name'])
        ext_tanium_unique_df = ext_tanium_df.drop_duplicates(subset=['Name'])

        df3['Name_upper'] = df3['Name'].str.upper()
        tanium_unique_df['Name_upper'] = tanium_unique_df['Name'].str.upper()
        ext_tanium_unique_df['Name_upper'] = ext_tanium_unique_df['Name'].str.upper()
        # On ne fusionne que sur la clé pour éviter le conflit sur la colonne 'Name'
        df3 = pd.merge(df3, tanium_unique_df[['Name_upper']], on='Name_upper', how='left', indicator=True)
        df3 = pd.merge(df3, ext_tanium_unique_df.rename(columns={'Observations': 'Situation fichier suivi'})[['Situation fichier suivi', 'Name_upper']], on='Name_upper', how='left')
        df3.drop(columns=['Name_upper'], inplace=True)
        
        df3['Tanium déployé ?'] = np.where(df3['_merge'] == 'both', df3['Name'], '#N/A')
        df3['OS Conforme ?'] = get_os_compliance_win10_plus(df3['OperatingSystemVersion'])
        df3['Résultat'] = np.where((df3['Tanium déployé ?'] == '#N/A') | (df3['OS Conforme ?'] == 'NOK'), 'NOK', 'OK')
        pattern_tanium_ok = 'Remonte sur Intune|TN installé'
        cond_suivi_ok = df3['Situation fichier suivi'].str.contains(pattern_tanium_ok, case=False, na=False)
        cond_resultat_ok = (df3['Résultat'] == 'OK')
        df3['Résultat final'] = np.where(cond_suivi_ok | cond_resultat_ok, 'OK', 'NOK')
        df3['LastLogonDate_short'] = df3['LastLogonDate'].dt.strftime('%Y-%m-%d')
        results.append({
            'title': "Conformité de l'agent Tanium",
            'dataframe': df3,
            'display_columns': [
                {'key': 'LastLogonDate_short', 'label': "Dernière Connexion"},
                {'key': 'Name', 'label': "Nom du Poste"},
                {'key': 'OS Conforme ?', 'label': "OS Conforme ?"},
                {'key': 'Tanium déployé ?', 'label': "Tanium Déployé ?"},
                {'key': 'Situation fichier suivi', 'label': "Observations Suivi"},
                {'key': 'Résultat final', 'label': "Résultat Final"}
            ],
            'summary_stats': {
                'Nb total Postes': len(base_df.copy()),
                'Non Conformes (NOK)': len(df3[df3['Résultat final'] == 'NOK']),
                'Taux de conformité ': f"{ (( len(df3[df3['Résultat final'] == 'OK'])/len(base_df.copy()) ) * 100):.2f}%",
            }
        })
        
        # 4. Conformité agent CrowdStrike
        df4 = base_df.copy()
        crowdstrike_df.rename(columns={'Hostname': 'Name'}, inplace=True)
        crowdstrike_unique_df = crowdstrike_df.drop_duplicates(subset=['Name'])
        ext_crowdstrike_unique_df = ext_crowdstrike_df.drop_duplicates(subset=['Name'])

        df4['Name_upper'] = df4['Name'].str.upper()
        crowdstrike_unique_df['Name_upper'] = crowdstrike_unique_df['Name'].str.upper()
        ext_crowdstrike_unique_df['Name_upper'] = ext_crowdstrike_unique_df['Name'].str.upper()
        # On ne fusionne que sur la clé pour éviter le conflit sur la colonne 'Name'
        df4 = pd.merge(df4, crowdstrike_unique_df[['Name_upper']], on='Name_upper', how='left', indicator=True)
        df4 = pd.merge(df4, ext_crowdstrike_unique_df.rename(columns={'Observations': 'Situation fichier suivi'})[['Situation fichier suivi', 'Name_upper']], on='Name_upper', how='left')
        df4.drop(columns=['Name_upper'], inplace=True)

        df4['CrowdStrike déployé ?'] = np.where(df4['_merge'] == 'both', df4['Name'], '#N/A')
        df4['OS Conforme ?'] = get_os_compliance_win10_plus(df4['OperatingSystemVersion'])
        df4['Résultat'] = np.where((df4['CrowdStrike déployé ?'] == '#N/A') | (df4['OS Conforme ?'] == 'NOK'), 'NOK', 'OK')
        pattern_cs_ok = 'Remonte sur Intune|CS installé'
        cond_suivi_ok_cs = df4['Situation fichier suivi'].str.contains(pattern_cs_ok, case=False, na=False)
        cond_resultat_ok_cs = (df4['Résultat'] == 'OK')
        df4['Résultat final'] = np.where(cond_suivi_ok_cs | cond_resultat_ok_cs, 'OK', 'NOK')
        df4['LastLogonDate_short'] = df4['LastLogonDate'].dt.strftime('%Y-%m-%d')
        results.append({
            'title': "Conformité de l'agent CrowdStrike",
            'dataframe': df4,
            'display_columns': [
                {'key': 'LastLogonDate_short', 'label': "Dernière Connexion"},
                {'key': 'Name', 'label': "Nom du Poste"},
                {'key': 'OS Conforme ?', 'label': "OS Conforme ?"},
                {'key': 'CrowdStrike déployé ?', 'label': "CrowdStrike Déployé ?"},
                {'key': 'Situation fichier suivi', 'label': "Observations Suivi"},
                {'key': 'Résultat final', 'label': "Résultat Final"}
            ],
            'summary_stats': {
                'Nb total Postes': len(base_df.copy()),
                'Non Conformes (NOK)': len(df4[df4['Résultat final'] == 'NOK']),
                'Taux de conformité ': f"{ (( len(df4[df4['Résultat final'] == 'OK'])/len(base_df.copy()) ) * 100):.2f}%",
            }
        })
        
        # 5. Conformité agent LAPS
        df5 = base_df.copy()
        laps_unique_df = laps_df.drop_duplicates(subset=['Name'])
        ext_laps_unique_df = ext_laps_df.drop_duplicates(subset=['Name'])
        
        df5['Name_upper'] = df5['Name'].str.upper()
        laps_unique_df['Name_upper'] = laps_unique_df['Name'].str.upper()
        ext_laps_unique_df['Name_upper'] = ext_laps_unique_df['Name'].str.upper()
        # On ne fusionne que sur la clé pour éviter le conflit sur la colonne 'Name'
        df5 = pd.merge(df5, laps_unique_df[['Name_upper']], on='Name_upper', how='left', indicator=True)
        df5 = pd.merge(df5, ext_laps_unique_df.rename(columns={'Observations': 'Situation fichier suivi'})[['Situation fichier suivi', 'Name_upper']], on='Name_upper', how='left')
        df5.drop(columns=['Name_upper'], inplace=True)

        df5['LAPS déployé ?'] = np.where(df5['_merge'] == 'both', df5['Name'], '#N/A')
        df5['OS Conforme ?'] = get_os_compliance_win10_plus(df5['OperatingSystemVersion'])
        df5['Résultat'] = np.where((df5['LAPS déployé ?'] == '#N/A') | (df5['OS Conforme ?'] == 'NOK'), 'NOK', 'OK')
        pattern_laps_ok = 'Remonte sur Intune|Laps installé'
        cond_suivi_ok_laps = df5['Situation fichier suivi'].str.contains(pattern_laps_ok, case=False, na=False)
        cond_resultat_ok_laps = (df5['Résultat'] == 'OK')
        df5['Résultat final'] = np.where(cond_suivi_ok_laps | cond_resultat_ok_laps, 'OK', 'NOK')
        df5['LastLogonDate_short'] = df5['LastLogonDate'].dt.strftime('%Y-%m-%d')
        results.append({
            'title': "Conformité de l'agent LAPS",
            'dataframe': df5,
            'display_columns': [
                {'key': 'LastLogonDate_short', 'label': "Dernière Connexion"},
                {'key': 'Name', 'label': "Nom du Poste"},
                {'key': 'OS Conforme ?', 'label': "OS Conforme ?"},
                {'key': 'LAPS déployé ?', 'label': "LAPS Déployé ?"},
                {'key': 'Situation fichier suivi', 'label': "Observations Suivi"},
                {'key': 'Résultat final', 'label': "Résultat Final"}
            ],
            'summary_stats': {
                'Nb total Postes': len(base_df.copy()),
                'Non Conformes (NOK)': len(df5[df5['Résultat final'] == 'NOK']),
                'Taux de conformité ': f"{ (( len(df5[df5['Résultat final'] == 'OK'])/len(base_df.copy()) ) * 100):.2f}%",
            }
        })

    except Exception as e:
        # Imprime l'erreur de manière plus détaillée pour le débogage
        import traceback
        print(f"Une erreur est survenue durant l'exécution du script : {e}")
        traceback.print_exc()
        raise e

    return results