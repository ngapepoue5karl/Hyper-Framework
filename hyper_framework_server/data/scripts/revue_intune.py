# revue_intune.py / analyse_multi_equipements.py

# === 1. Définition des entrées ===
__hyper_inputs__ = [
    {"key": "intune_file", "label": "Fichier Intune - Devices (.csv)"},
    {"key": "ad_users", "label": "Export des utilisateurs AD (.txt)"},  # Mise à jour pour indiquer .txt
    {"key": "glpi_data", "label": "Données GLPI (.csv)"}
]

import pandas as pd
import numpy as np
import chardet
import re
import os

# =============================================================================
# PHASE 1 : FONCTIONS DE NETTOYAGE ET DE PRÉPARATION
# =============================================================================

def nettoyer_fichier_intune(input_file):
    """Charge et nettoie le fichier Intune (séparateur virgule)."""
    with open(input_file, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']
    return pd.read_csv(input_file, sep=",", quotechar='"', encoding=encoding, low_memory=False)

def nettoyer_fichier_ad(input_file):
    """Charge et nettoie le fichier AD Users (séparateur point-virgule, sans en-tête)."""
    with open(input_file, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']
               
    headers = [
        "CN", "Created", "Description", "EmployeeNumber", "Enabled", "Modified", "Title", 
        "LastLogonDate", "Name", "DisplayName", "ObjectClass", "ObjectGUID", "PasswordExpired", 
        "PasswordLastSet", "PasswordNotRequired", "SamAccountName", "SID", "Surname", 
        "UserPrincipalName", "MemberOf", "Office", "PasswordNeverExpires", "LockedOut", 
        "LockoutTime", "AccountExpirationDate", "Department", "Description2_placeholder", "Enabled2"
    ]
    df = pd.read_csv(input_file, sep=';', header=None, names=headers, encoding=encoding, quotechar='"', low_memory=False)
    
    # La colonne 'Description2' est une copie de 'Description'
    df['Description2'] = df['Description']
    df = df.drop(columns=['Description2_placeholder'])
    
    return df

def nettoyer_fichier_glpi(input_file):
    """Charge et nettoie le fichier GLPI (séparateur point-virgule)."""
    with open(input_file, 'rb') as f:
        encoding = chardet.detect(f.read())['encoding']
    
    headers = [
        "Nom", "Entité", "Lieu", "Statut", "Numéro de série", "Utilisateur", 
        "Fournisseur", "Fabricant", "Dernière modification", "Commentaires", 
        "Groupe", "ID", "Nb documents", "Usager numéro", "Type d'élément"
    ]
    return pd.read_csv(input_file, sep=';', names=headers, encoding=encoding, quotechar='"', skiprows=1, low_memory=False)

# ===============================
#  CORRECTION APPLIQUÉE ICI
# ===============================
def creer_fichier_intermediaire(intune_df, ad_df, glpi_df, fichier_sortie_path):
    """
    Combine les 3 DataFrames pour créer le fichier intermédiaire avec la structure finale.
    """
    df = intune_df.copy()

    # 1. Enrichissement avec GLPI
    glpi_subset = glpi_df[['Nom', 'Entité']].drop_duplicates(subset=['Nom'])
    df = pd.merge(df, glpi_subset, left_on='Device name', right_on='Nom', how='left')
    df.rename(columns={'Entité': 'Localisation équipement'}, inplace=True)
    
    # 2. Enrichissement avec AD (CORRIGÉ)
    # On sélectionne les colonnes nécessaires depuis AD, y compris 'Description2' et 'Department'
    ad_subset = ad_df[['UserPrincipalName', 'Office', 'Description2', 'Department']].drop_duplicates(subset=['UserPrincipalName'])
    df = pd.merge(df, ad_subset, left_on='Primary user email address', right_on='UserPrincipalName', how='left')
    
    # On renomme les colonnes selon les nouvelles règles :
    # 'Propriétaire' vient de 'Description2'
    # 'Localisation Propriétaire' vient de 'Office'
    df.rename(columns={'Office': 'Localisation Propriétaire', 'Description2': 'Propriétaire'}, inplace=True)

    # 3. Calcul de "Types d'appareils"
    conditions_type = [
        (df['Device name'].str.contains("CMRL|CMRU|CMRT", case=False, na=False)),
        (df['OS'].str.contains("Windows", case=False, na=False))
    ]
    choix_type = ["Équipement SABC", "Ordinateur Personnel"]
    df["Types d'appareils"] = np.select(conditions_type, choix_type, default="Smartphones")

    # 4. Calcul de "Sites" (CORRIGÉ)
    # 'Sites' vient en priorité de la colonne 'Department' du fichier AD.
    # S'il n'y a pas de valeur, on la calcule à partir de la localisation de l'équipement (GLPI).
    conditions_site = [
        (df['Localisation équipement'].str.contains("SIEGE", na=False)), (df['Localisation équipement'].str.contains("CENTRE", na=False)),
        (df['Localisation équipement'].str.contains("GCSA", na=False)), (df['Localisation équipement'].str.contains("OUEST", na=False)),
        (df['Localisation équipement'].str.contains("LITTORAL", na=False)), (df['Localisation équipement'].str.contains("NORD", na=False))
    ]
    choix_site = ["SIEGE", "DR CENTRE", "GCSA", "DR OUEST", "DR LITTORAL", "DR NORD"]
    sites_from_glpi = np.select(conditions_site, choix_site, default="Non trouvé")
    
    df['Sites'] = df['Department'].fillna(pd.Series(sites_from_glpi, index=df.index))

    # --- Finalisation de la structure ---
    colonnes_finales = [
        'Device ID', 'Device name', 'Enrollment date', 'Last check-in', 'Azure AD Device ID', 'OS version', 
        'Azure AD registered', 'EAS activation ID', 'Serial number', 'Manufacturer', 'Model', 'EAS activated', 
        'IMEI', 'Last EAS sync time', 'EAS reason', 'EAS status', 'Compliance grace period expiration', 
        'Security patch level', 'Wi-Fi MAC', 'MEID', 'Subscriber carrier', 'Total storage', 'Free storage', 
        'Management name', 'Category', 'UserId', 'Primary user UPN', 'Primary user email address', 
        'Primary user display name', 'WiFiIPv4Address', 'WiFiSubnetID', 'Compliance', 'Managed by', 'Ownership', 
        'Device state', 'Intune registered', 'Supervised', 'Encrypted', 'OS', 'SkuFamily', 'JoinType', 
        'Phone number', 'Jailbroken', 'ICCID', 'EthernetMAC', 'CellularTechnology', 'ProcessorArchitecture', 
        'EID', 'SystemManagementBIOSVersion', 'TPMManufacturerId', 'TPMManufacturerVersion', "Types d'appareils",
        'Localisation équipement', 'Localisation Propriétaire', 'Propriétaire', 'Sites'
    ]
    
    for col in colonnes_finales:
        if col not in df.columns:
            df[col] = pd.NA

    df_final = df[colonnes_finales]
    df_final.to_excel(fichier_sortie_path, index=False)
    print(f"Fichier intermédiaire créé avec succès : {fichier_sortie_path}")
    return df_final

# =============================================================================
# PHASE 2 : FONCTION DE TRAITEMENT FINAL (Inchangée)
# =============================================================================

def traiter_fichier_excel(fichier_entree, fichier_sortie):
    # Charger le fichier Excel
    df = pd.read_excel(fichier_entree)
    
    # Vérifier que les colonnes nécessaires existent
    colonnes_attendues = ['Propriétaire', "Types d'appareils", 'Manufacturer', 'Model', 'Serial number']
    if not all(col in df.columns for col in colonnes_attendues):
        raise ValueError(f"Les colonnes attendues ne sont pas présentes dans le fichier. Colonnes trouvées: {df.columns}")
    
    # Créer la colonne Device name en concaténant Manufacturer, Model et Serial number
    df['Device name'] = df['Manufacturer'].astype(str) + ' ' + df['Model'].astype(str) + ' (SN: ' + df['Serial number'].astype(str) + ')'
    
    # Supprimer les doublons dans la colonne Device name
    df = df.drop_duplicates(subset=['Device name'])
    
    # Compter le nombre total d'équipements par propriétaire
    df_count = df.groupby('Propriétaire')['Types d\'appareils'].count().reset_index()
    df_count.rename(columns={'Types d\'appareils': 'Nombre total équipements'}, inplace=True)
    
    # Compter le nombre de chaque type d'équipement par propriétaire
    df_device_count = df.pivot_table(index='Propriétaire', columns='Types d\'appareils', aggfunc='size', fill_value=0).reset_index()
    df_device_count.rename(columns={
        'Smartphone': 'Nombre de smartphones', 
        'Ordinateur personnel': 'Nombre d\'ordinateurs'
    }, inplace=True)
    
    # Fusionner les données
    df_final = df_count.merge(df_device_count, on='Propriétaire', how='left').fillna(0)
    
    # Filtrer uniquement les propriétaires ayant plus d'un équipement
    df_final = df_final[df_final['Nombre total équipements'] > 1]
    
    # Filtrer les équipements des propriétaires sélectionnés et mettre chaque device name sur une nouvelle ligne
    df_filtree = df[df['Propriétaire'].isin(df_final['Propriétaire'])][['Propriétaire', 'Device name']]
    
    # Trier les résultats par Propriétaire
    df_final = df_final.sort_values(by=['Propriétaire'])
    df_filtree = df_filtree.sort_values(by=['Propriétaire'])
    
    # Créer un fichier Excel avec deux feuilles
    with pd.ExcelWriter(fichier_sortie) as writer:
        df_final.to_excel(writer, sheet_name='Nombre équipements', index=False)
        df_filtree.to_excel(writer, sheet_name='Modèles multiples', index=False)
    return df_final, len(df)

# =============================================================================
# PHASE 3 : FONCTION PRINCIPALE RUN (Inchangée)
# =============================================================================

def run(input_file_paths, output_dir_path):
    results = []
    try:
        # --- Étape 1 : Chargement des fichiers sources ---
        intune_df = nettoyer_fichier_intune(input_file_paths.get('intune_file'))
        ad_df = nettoyer_fichier_ad(input_file_paths.get('ad_users'))
        glpi_df = nettoyer_fichier_glpi(input_file_paths.get('glpi_data'))

        # --- Étape 2 : Création du fichier intermédiaire ---
        fichier_intermediaire_path = os.path.join(output_dir_path, "donnees_unifiees_pour_analyse.xlsx")
        creer_fichier_intermediaire(intune_df, ad_df, glpi_df, fichier_intermediaire_path)

        # --- Étape 3 : Traitement du fichier intermédiaire ---
        fichier_rapport_final_path = os.path.join(output_dir_path, "rapport_final_multi_equipements.xlsx")
        df_resultat, _ = traiter_fichier_excel(fichier_intermediaire_path, fichier_rapport_final_path)

        # --- Étape 4 : Calcul des statistiques pour l'affichage ---
        nb_total_proprietaires = df_resultat['Propriétaire'].nunique()
        nb_pers_multi_equip = len(df_resultat[df_resultat['Nombre total équipements'] >= 3])
        nb_pers_conformes = len(df_resultat[df_resultat['Nombre total équipements'] <= 2])
        taux_conformite = (nb_pers_conformes / nb_total_proprietaires * 100) if nb_total_proprietaires > 0 else 0

        # --- Étape 5 : Structuration du résultat pour l'Hyper-Framework ---
        colonnes_finales_affichage = {
            'Propriétaire': 'Propriétaire',
            'Nombre total équipements': 'Nombre total équipements',
            'Ordinateur Personnel': 'Ordinateur Personnel',
            'Smartphones': 'Smartphones',
            'Équipement SABC': 'Équipement SABC'
        }
        for col in colonnes_finales_affichage.keys():
            if col not in df_resultat.columns:
                df_resultat[col] = 0
        
        results.append({
            'title': "Analyse des équipements multiples par propriétaire",
            'dataframe': df_resultat,
            'display_columns': [
                {'key': k, 'label': v} for k, v in colonnes_finales_affichage.items()
            ],
            'summary_stats': {
                'Nb Total Propriétaire Intune': nb_total_proprietaires,
                'Nb de pers ayant >=3 équip.': nb_pers_multi_equip,
                'Taux de conformité': f"{taux_conformite:.2f}%"
            }
        })
        
    except Exception as e:
        print(f"Une erreur est survenue durant l'analyse : {e}")
        raise e
    
    return results