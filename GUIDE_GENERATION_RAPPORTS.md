# Guide de Génération des Rapports Word

## Vue d'Ensemble

Ce guide explique comment Hyper-Framework génère automatiquement des rapports Word professionnels à partir de vos scripts de contrôle. Les rapports sont créés au format DOCX et incluent un en-tête personnalisé, des graphiques, des tableaux de données, et des sections à compléter manuellement.

---

## Processus de Génération Automatique

### Déclenchement

Les rapports sont générés **automatiquement** après chaque exécution d'analyse :

1. L'utilisateur lance un contrôle depuis l'interface client
2. Le script s'exécute et retourne les résultats
3. Le framework génère un fichier Excel avec les données détaillées
4. **Un rapport Word est créé automatiquement** dans le dossier `Outputs/`
5. L'utilisateur peut télécharger le rapport via l'interface

### Emplacement des Rapports

```
    Outputs/
    ├── NomDuControle_20251221_143025/
    │   ├── output.xlsx              # Données Excel détaillées
    │   └── rapport.docx             # Rapport Word généré
```

Le nom du dossier suit le format : `NomDuControle_YYYYMMDD_HHMMSS`

---

## Structure Complète d'un Rapport

Un rapport généré contient les sections suivantes :

### 1. En-tête (Automatique)

L'en-tête est un tableau complexe de 4 lignes × 7 colonnes comprenant :

**Ligne 1 :**
- Logo de l'organisation (colonne 1)
- Titre du contrôle (colonnes 2-5)
- Code du contrôle avec date (colonnes 6-7)

**Ligne 2 :** En-têtes des métadonnées
- Application concernée
- Couche concernée
- Référence du risque
- Nom du risque
- Conclusion
- Nom du contrôle (colonnes 6-7)

**Ligne 3 :** Données du contrôle (automatiques si métadonnées fournies)
- Valeurs pour chaque colonne selon `__hyper_control_metadata__`

**Ligne 4 :** Informations complémentaires
- Destinataire (colonnes 1-3)
- Ref Description (colonnes 4-5)
- Code PS3 (colonnes 6-7)

### 2. Description du contrôle (Automatique)

Reprend le champ `"description"` de `__hyper_control_metadata__`.

**Exemple :**
```
Description du contrôle :
Vérifier que la synchronisation des données des utilisateurs de SABC est activée sur OneDrive.
```

### 3. Analyse (Automatique)

Reprend le champ `"analyse"` de `__hyper_control_metadata__`.

**Exemple :**
```
Analyse :
Ressortir les utilisateurs dont les données n'ont pas été synchronisées sur OneDrive 
au cours des 30 derniers jours.
```

### 4. Résultats (Automatique)

Cette section est générée à partir des données retournées par votre fonction `run()` :

#### 4.1 Statistiques Clés

Liste à puces des `summary_stats` :

```
Statistiques Clés
• Les utilisateurs actifs: 3046
• Les utilisateurs Assujettis: 2581
• Les utilisateurs avec licence: 2445
• Les utilisateurs NOK: 9
• Taux: 99.63%
```

#### 4.2 Graphiques

Inclut les graphiques définis dans `__hyper_charts__` (voir GUIDE_GRAPHIQUES_VEGALITE.md).

#### 4.3 Données Détaillées

Tableau avec les colonnes spécifiées dans `display_columns` (limité à 60 lignes).

### 5. Recommandations (Manuel)

Section vide à remplir manuellement par l'auditeur.

### 6. Évidence de suivi des exceptions (Manuel)

Section vide à remplir manuellement par l'auditeur.

### 7. Tableau de Signatures (Automatique)

Tableau de signatures avec les informations de l'utilisateur :
- Nom et prénom de l'auditeur
- Date d'exécution
- Espaces pour signatures du validateur et approbateur

### 8. Pied de Page (Automatique)

- Numéro de page centré
- Format : `Page X sur Y`

---

## Configuration pour un Rapport Complet

### Étape 1 : Définir les Métadonnées

Au début de votre script, définissez `__hyper_control_metadata__` :

```python
    __hyper_control_metadata__ = {
        "control_code_prefix": "CTL_SSI_02_SAVE",
        "application": "OneDrive",
        "layer": "Données",
        "risk_reference": "R182, R211",
        "risk_name": "Indisponibilité du système d'information\nPerte des données",
        "control_name": "Sauvegarde des données des PCs",
        "ref_description": "CTL_SSI_DON_SAVE_2",
        "description": "Vérifier que la synchronisation des données des utilisateurs de SABC est activée sur OneDrive.",
        "analyse": "Ressortir les utilisateurs dont les données n'ont pas été synchronisées sur OneDrive au cours des 30 derniers jours."
    }
```

Pour plus de détails, voir [GUIDE_METADONNEES_CONTROLE.md](GUIDE_METADONNEES_CONTROLE.md).

### Étape 2 : Définir les Graphiques (Optionnel)

```python
__hyper_charts__ = [
    {
        "type": "bar",
        "title": "Vue d'ensemble des utilisateurs",
        "keys": ["Les utilisateurs actifs", "Les utilisateurs Assujettis", "Les utilisateurs avec licence"],
        "colors": ["#4CAF50", "#2196F3", "#FF9800"],
        "orientation": "vertical"
    },
    {
        "type": "pie",
        "title": "Conformité des sauvegardes",
        "keys": ["Les utilisateurs avec licence", "Les utilisateurs NOK"],
        "colors": ["#4CAF50", "#F44336"]
    },
    {
        "type": "gauge",
        "title": "Taux de conformité",
        "key": "Taux",
        "max_value": 100,
        "colors": ["#F44336", "#FF9800", "#4CAF50"],
        "thresholds": [90, 95]
    }
]
```

Pour plus de détails, voir [GUIDE_GRAPHIQUES_VEGALITE.md](GUIDE_GRAPHIQUES_VEGALITE.md).

### Étape 3 : Structurer les Résultats Retournés

Votre fonction `run()` doit retourner une liste de dictionnaires avec cette structure :

```python
def run(input_file_paths: dict, output_dir_path: str):
    # ... votre traitement ...
    
    return [{
        "title": "Sauvegardes des données PCs",
        "excel_output": out_xlsx,  # Chemin du fichier Excel
        "dataframe": df_results,   # DataFrame pour l'interface
        "display_columns": [       # Colonnes à afficher
            {"key": "Username", "label": "Nom d'utilisateur"},
            {"key": "LastSync", "label": "Dernière synchronisation"},
            {"key": "Status", "label": "Statut"}
        ],
        "summary_stats": {         # Statistiques résumées
            "Les utilisateurs actifs": 3046,
            "Les utilisateurs Assujettis": 2581,
            "Les utilisateurs avec licence": 2445,
            "Les utilisateurs NOK": 9,
            "Taux": "99.63%"
        },
        "chart_configs": __hyper_charts__  # Vos graphiques définis
    }]
```

**Champs obligatoires :**
- `title` : Titre de la section dans le rapport
- `summary_stats` : Dictionnaire de statistiques clés

**Champs optionnels :**
- `dataframe` : DataFrame pandas pour affichage dans l'interface
- `display_columns` : Liste des colonnes à afficher dans le tableau
- `items` : Liste de dictionnaires (alternative au dataframe)
- `chart_configs` : Configuration des graphiques (généralement `__hyper_charts__`)
- `excel_output` : Chemin vers le fichier Excel généré

---

## Exemple Complet de Script

### Script : `sauvegarde_pcs.py`

```python
# === Configuration du contrôle ===

__hyper_inputs__ = [
    {"key": "onedrive_file", "label": "OneDriveUsageAccountDetail (.csv)"},
    {"key": "users_file", "label": "Users (.csv)"},
    {"key": "ad_file", "label": "Utilisateur AD (.txt)"}
]

__hyper_periodicity__ = 'WEEK'

__hyper_charts__ = [
    {
        "type": "bar",
        "title": "Vue d'ensemble des utilisateurs",
        "keys": ["Les utilisateurs actifs", "Les utilisateurs Assujettis", "Les utilisateurs avec licence"],
        "colors": ["#4CAF50", "#2196F3", "#FF9800"],
        "orientation": "vertical"
    },
    {
        "type": "pie",
        "title": "Conformité des sauvegardes",
        "keys": ["Les utilisateurs avec licence", "Les utilisateurs NOK"],
        "colors": ["#4CAF50", "#F44336"]
    },
    {
        "type": "gauge",
        "title": "Taux de conformité",
        "key": "Taux",
        "max_value": 100,
        "colors": ["#F44336", "#FF9800", "#4CAF50"],
        "thresholds": [90, 95]
    }
]

__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_02_SAVE",
    "application": "OneDrive",
    "layer": "Données",
    "risk_reference": "R182, R211",
    "risk_name": "Indisponibilité du système d'information\nPerte des données",
    "control_name": "Sauvegarde des données des PCs",
    "ref_description": "CTL_SSI_DON_SAVE_2",
    "description": "Vérifier que la synchronisation des données des utilisateurs de SABC est activée sur OneDrive.",
    "analyse": "Ressortir les utilisateurs dont les données n'ont pas été synchronisées sur OneDrive au cours des 30 derniers jours."
}

# === Code du contrôle ===

import pandas as pd
import os
from datetime import datetime, timedelta

def run(input_file_paths: dict, output_dir_path: str):
    """
    Exécute l'analyse des sauvegardes OneDrive.
    
    Args:
        input_file_paths: Dictionnaire des fichiers d'entrée
        output_dir_path: Chemin du dossier de sortie
        
    Returns:
        Liste de dictionnaires avec les résultats de l'analyse
    """
    # 1. Charger les données
    onedrive_df = pd.read_csv(input_file_paths['onedrive_file'])
    users_df = pd.read_csv(input_file_paths['users_file'])
    
    # 2. Effectuer l'analyse
    # ... votre logique métier ...
    
    # 3. Calculer les statistiques
    total_users = len(users_df)
    active_users = len(users_df[users_df['Status'] == 'Active'])
    licensed_users = len(onedrive_df[onedrive_df['HasLicense'] == True])
    nok_users = len(onedrive_df[onedrive_df['LastSync'] < datetime.now() - timedelta(days=30)])
    compliance_rate = (licensed_users - nok_users) / licensed_users * 100 if licensed_users > 0 else 0
    
    # 4. Créer le DataFrame des résultats
    results_df = onedrive_df[onedrive_df['LastSync'] < datetime.now() - timedelta(days=30)]
    
    # 5. Sauvegarder en Excel
    excel_path = os.path.join(output_dir_path, "output.xlsx")
    results_df.to_excel(excel_path, index=False)
    
    # 6. Retourner les résultats pour le rapport
    return [{
        "title": "Sauvegardes des données PCs",
        "excel_output": excel_path,
        "dataframe": results_df,
        "display_columns": [
            {"key": "Username", "label": "Nom d'utilisateur"},
            {"key": "Email", "label": "Email"},
            {"key": "LastSync", "label": "Dernière synchronisation"},
            {"key": "StorageUsed", "label": "Stockage utilisé (GB)"}
        ],
        "summary_stats": {
            "Les utilisateurs actifs": active_users,
            "Les utilisateurs Assujettis": total_users,
            "Les utilisateurs avec licence": licensed_users,
            "Les utilisateurs NOK": nok_users,
            "Taux": f"{compliance_rate:.2f}%"
        },
        "chart_configs": __hyper_charts__
    }]
```

---

## Personnalisation Avancée

### Format du Code du Contrôle dans l'En-tête

Le code affiché dans l'en-tête suit le format :

```
[control_code_prefix]_[YYYYMMDD]_[version]
```

**Exemple :**
- `control_code_prefix` : `"CTL_SSI_02_SAVE"`
- Date d'exécution : `20251221`
- Version : `3` (calculée automatiquement)

**Résultat :** `CTL_SSI_02_SAVE_20251221_3`

### Personnaliser le Logo

Le logo affiché dans l'en-tête provient de :

```
hyper_framework_server/assets/images/logo_default.png
```

**Dimensions recommandées :** 2,81 cm × 1,42 cm (environ 150×75 pixels)

Pour changer le logo :
1. Remplacez le fichier `logo_default.png`
2. Respectez les dimensions pour un rendu optimal

### Limitations du Tableau de Données

Par défaut, seules les **60 premières lignes** sont incluses dans le rapport Word pour éviter des fichiers trop lourds.

Une note est ajoutée automatiquement si plus de 60 lignes existent :

```
Note : Seules les 60 premières lignes sont affichées. 
Total de 150 lignes dans le fichier Excel complet.
```

**Pour modifier cette limite :**
Voir le fichier [report_service.py](hyper_framework_server/services/report_service.py#L1159) :

```python
max_rows = min(60, len(items))  # Modifier la valeur 60
```

---

## Styles et Formatage

### Polices Utilisées

**En-tête (tableau) :**
- Police : Tahoma
- Tailles : 6pt à 10pt selon les éléments
- Gras pour les titres

**Corps du document :**
- Police : Arial
- Tailles : 8pt pour le contenu et les titres
- Gras et souligné pour les titres de niveau 1

### Couleurs de l'Hexagone de Conclusion

L'hexagone dans l'en-tête change de couleur selon le taux de conformité :

| Taux de conformité | Couleur | Code HEX |
|-------------------|---------|----------|
| ≥ 95%             | Vert    | #4CAF50  |
| 50% - 94%         | Orange  | #FF9800  |
| < 50%             | Rouge   | #F44336  |

---

## Workflow Complet

### 1. Préparation du Script

```python
# Définir les métadonnées
__hyper_control_metadata__ = {...}

# Définir les graphiques
__hyper_charts__ = [...]

# Implémenter la fonction run()
def run(input_file_paths, output_dir_path):
    # ... logique ...
    return [{
        "title": "...",
        "summary_stats": {...},
        # ...
    }]
```

### 2. Exécution depuis l'Interface Client

1. Ouvrir l'application client Hyper-Framework
2. Se connecter avec vos identifiants
3. Sélectionner le contrôle à exécuter
4. Uploader les fichiers d'entrée requis
5. Cliquer sur "Lancer l'Analyse"

### 3. Génération Automatique

Le serveur :
1. Exécute votre script
2. Collecte les résultats
3. Génère le fichier Excel
4. **Génère automatiquement le rapport Word**
5. Enregistre tout dans `Outputs/`

### 4. Téléchargement et Consultation

1. Le client affiche un message de succès
2. Cliquer sur "Voir les Résultats" pour afficher les données
3. Cliquer sur "Télécharger Excel" pour le fichier de données
4. **Cliquer sur "Télécharger Rapport" pour le rapport Word**
5. Ouvrir le rapport avec Microsoft Word ou LibreOffice

### 5. Finalisation Manuelle

Ouvrir le rapport et compléter :
1. La section "Recommandations"
2. La section "Évidence de suivi des exceptions"
3. Les signatures si nécessaire

---

## Dépannage

### Le rapport n'est pas généré

**Causes possibles :**
1. Erreur dans le script avant la fin de l'exécution
2. Problème de droits d'écriture sur le dossier `Outputs/`
3. Absence de résultats retournés par `run()`

**Solutions :**
- Vérifier les logs du serveur dans l'interface client (onglet "Logs")
- S'assurer que `run()` retourne bien une liste de dictionnaires
- Vérifier les permissions du dossier `hyper_framework_server/data/`

### L'en-tête ne contient que "N/A"

**Cause :** Les métadonnées ne sont pas définies ou mal formatées

**Solution :**
- Vérifier que `__hyper_control_metadata__` est défini au niveau du module
- Vérifier l'orthographe exacte des clés (sensible à la casse)
- S'assurer que tous les champs requis sont présents

### Les graphiques ne s'affichent pas

**Causes possibles :**
1. `chart_configs` n'est pas fourni dans les résultats
2. Les clés dans `__hyper_charts__` ne correspondent pas aux `summary_stats`
3. Erreur lors de la génération de l'image

**Solutions :**
- Vérifier que `chart_configs: __hyper_charts__` est dans le dictionnaire retourné
- Vérifier la correspondance exacte des clés (voir GUIDE_GRAPHIQUES_VEGALITE.md)
- Consulter les logs pour les erreurs matplotlib

### Le tableau de données est vide

**Causes possibles :**
1. `items` ou `dataframe` non fourni
2. `display_columns` mal défini
3. DataFrame vide

**Solutions :**
- S'assurer de fournir soit `dataframe` soit `items` dans les résultats
- Vérifier que les clés dans `display_columns` correspondent aux colonnes du DataFrame
- Vérifier que le DataFrame contient des données

### Erreur "Impossible de sauvegarder le fichier"

**Causes possibles :**
1. Chemin de sauvegarde invalide
2. Droits d'accès insuffisants
3. Fichier déjà ouvert dans Word

**Solutions :**
- Vérifier que le dossier de sortie existe
- S'assurer que le processus a les droits d'écriture
- Fermer le fichier Word s'il est déjà ouvert

### Le logo ne s'affiche pas

**Cause :** Le fichier `logo_default.png` est manquant

**Solution :**
- Placer un fichier PNG valide dans `hyper_framework_server/assets/images/`
- Nom exact : `logo_default.png`
- Dimensions recommandées : 150×75 pixels

---

## Exemples de Résultats

### Exemple 1 : Analyse Simple

```python
return [{
    "title": "Résultats de l'analyse",
    "summary_stats": {
        "Total d'éléments analysés": 100,
        "Éléments conformes": 95,
        "Éléments non-conformes": 5,
        "Taux de conformité": "95%"
    }
}]
```

**Rapport généré :**
- En-tête avec métadonnées
- Description et Analyse
- Statistiques sous forme de liste
- Sections vides pour recommandations
- Signatures

### Exemple 2 : Analyse avec Graphiques

```python
return [{
    "title": "Analyse de conformité",
    "summary_stats": {
        "Conforme": 95,
        "Non conforme": 5,
        "Taux": "95%"
    },
    "chart_configs": [
        {
            "type": "pie",
            "title": "Répartition",
            "keys": ["Conforme", "Non conforme"],
            "colors": ["#4CAF50", "#F44336"]
        }
    ]
}]
```

**Rapport généré :**
- Tout l'exemple 1
- **Plus** : Graphique circulaire intégré

### Exemple 3 : Analyse avec Données Détaillées

```python
return [{
    "title": "Utilisateurs non conformes",
    "summary_stats": {
        "Total utilisateurs": 100,
        "Non conformes": 5
    },
    "dataframe": df_nok,
    "display_columns": [
        {"key": "Username", "label": "Nom d'utilisateur"},
        {"key": "Reason", "label": "Raison"}
    ]
}]
```

**Rapport généré :**
- Tout l'exemple 1
- **Plus** : Tableau avec les 5 utilisateurs non conformes

---

## Bonnes Pratiques

### 1. Toujours Définir les Métadonnées

Même si certains champs peuvent être "N/A", définissez toujours `__hyper_control_metadata__` pour un rapport complet.

### 2. Limiter la Taille des DataFrames

Pour les analyses avec beaucoup de lignes :
- Créez un DataFrame filtré pour l'interface (top 60)
- Gardez toutes les données dans le fichier Excel

```python
# DataFrame complet pour Excel
full_df.to_excel(excel_path)

# DataFrame filtré pour le rapport
display_df = full_df.head(60)

return [{
    "dataframe": display_df,  # Seulement 60 lignes
    "excel_output": excel_path  # Toutes les lignes
}]
```

### 3. Statistiques Significatives

Choisissez des statistiques qui donnent une vue d'ensemble claire :

```python
summary_stats = {
    "Total analysé": total,
    "Conformes": conforme,
    "Non conformes": non_conforme,
    "Taux de conformité": f"{taux:.2f}%",
    "Dernière mise à jour": date_str
}
```

### 4. Noms de Colonnes Clairs

Utilisez des labels descriptifs dans `display_columns` :

```python
display_columns = [
    {"key": "usr", "label": "Nom d'utilisateur"},  # Meilleur que "usr"
    {"key": "lst_sync", "label": "Dernière synchronisation"},  # Meilleur que "lst_sync"
]
```

### 5. Gérer les Erreurs

Toujours gérer les cas où les données sont absentes :

```python
def run(input_file_paths, output_dir_path):
    try:
        # ... traitement ...
        
        return [{
            "title": "Résultats",
            "summary_stats": summary_stats or {}
        }]
    except Exception as e:
        # Logger l'erreur
        print(f"Erreur : {e}")
        return [{
            "title": "Erreur",
            "summary_stats": {"Message": str(e)}
        }]
```

---

## Références

- **Métadonnées du contrôle :** Voir [GUIDE_METADONNEES_CONTROLE.md](GUIDE_METADONNEES_CONTROLE.md)
- **Configuration des graphiques :** Voir [GUIDE_GRAPHIQUES_VEGALITE.md](GUIDE_GRAPHIQUES_VEGALITE.md)
- **Code source :** Voir [report_service.py](hyper_framework_server/services/report_service.py)

---

## Support et Assistance

Pour toute question ou problème :
1. Consulter la section Dépannage ci-dessus
2. Vérifier les logs du serveur dans l'interface client
3. Contacter l'administrateur système

---

**Date de création :** 5 décembre 2025  
**Version :** 1.0  
**Auteur :** Karl Popper