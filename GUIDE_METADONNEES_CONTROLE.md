# Guide des Métadonnées de Contrôle

## Vue d'Ensemble

Ce guide explique comment définir les métadonnées d'un contrôle pour personnaliser l'en-tête des rapports générés automatiquement.

---

## Structure des Métadonnées

Chaque script de contrôle doit définir une variable `__hyper_control_metadata__` contenant un dictionnaire avec les champs suivants :

```python
__hyper_control_metadata__ = {
    "application": "Nom des applications",       # Applications concernées
    "layer": "Couche",                          # Couche concernée (Physique, Données, Application, etc.)
    "risk_reference": "R123, R456",             # Références des risques 
    "risk_name": "Nom du risque",               # Nom du risque 
    "control_name": "Nom du contrôle",          # Nom complet du contrôle
    "ref_description": "CTL_SSI_XXX_XXX_X",     # Référence de description
    "description": "Description du contrôle",   # Description détaillée du contrôle
    "analyse": "Points d'analyse du contrôle"   # Liste des points d'analyse (peut être multiligne)
}
```

---

## Champs Détaillés

### 1. `application`
**Format :** Du texte
Les applications ou systèmes concernés par le contrôle.

**Exemples :**
- `"OneDrive"`
- `"CrowdStrike, Tanium, AD"`
- `"CrowdStrike, Tanium, AD, GLPI, Intune"`

### 2. `layer`
**Format :** Du texte
La couche du système d'information concernée.

**Exemples courants :**
- `"Données"`
- `"Physique"`
- `"Application"`
- `"Réseau"`

### 3. `risk_reference`
**Format :** `RXX, RYY` 
Les références des risques couverts par le contrôle.

**Exemples :**
- `"R182, R211"`
- `"R24"`
- `"R45, R67, R89"`

### 4. `risk_name`
**Format :** Du texte
Le nom ou la description du risque. 

**Exemples :**
- `"Absence de contrôle efficace de modification de configuration"`
- `"Indisponibilité du système d'information\nPerte des données"` 

### 5. `control_name`
**Format :** Du texte
Le nom complet et descriptif du contrôle.

**Exemples :**
- `"Sauvegarde des données des PCs"`
- `"Conformité des terminaux"`
- `"Conformité des serveurs"`

### 6. `ref_description`
**Format :** `CTL_SSI_XXX_XXX_X`
La référence de description du contrôle.
**Exemples :**
- `"CTL_SSI_DON_SAVE_2"`
- `"CTL_SSI_PHY_TMO_1"`
- `"CTL_SSI_PHY_SRV_1"`

### 7. `description`
**Format :** Du texte
La description détaillée du contrôle expliquant son objectif.

**Exemples :**
- `"Vérifier que la synchronisation des données des utilisateurs de SABC est activée sur OneDrive."`
- `"Ce contrôle a pour but d'assurer le suivi de la conformité des terminaux mis à la disposition du personnel du Groupe SABC."`
- `"Ce contrôle a pour but d'assurer le suivi de la conformité des serveurs du Groupe SABC."`

### 8. `analyse`
**Format :** Du texte

La liste des points d'analyse effectués par le contrôle. Pour les listes à puces, utiliser le caractère `•`.

**Exemple :**
`"Ressortir les utilisateurs dont les données n'ont pas été synchronisées sur OneDrive au cours des 30 derniers jours."`

---

## Exemple Complet

### Exemple : Sauvegarde des PCs

```python
# sauvegarde_pcs.py

__hyper_inputs__ = [
    {"key": "onedrive_file", "label": "OneDriveUsageAccountDetail (.csv)"},
    {"key": "users_file", "label": "Users (.csv)"},
    {"key": "ad_file", "label": "Utilisateur AD (.txt)"}
]

__hyper_periodicity__ = 'WEEK'

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

# ... reste du script ...
```
---



## Placement dans le Script

Les métadonnées doivent être placées **au début du fichier**, juste après les autres variables spéciales :

```python
# 1. Définition des inputs
__hyper_inputs__ = [...]

# 2. Périodicité 
__hyper_periodicity__ = 'WEEK'

# 3. Configuration des graphiques (optionnel)
__hyper_charts__ = [...]

# 4. MÉTADONNÉES DU CONTRÔLE 
__hyper_control_metadata__ = {
    "control_code_prefix": "...",
    "application": "...",
    # ... autres champs ...
}

# 5. Imports et reste du code
import pandas as pd
# ...
```


## Validation

### Vérifier que les Métadonnées Fonctionnent

1. Exécutez votre contrôle depuis l'interface client
2. Attendez la génération du rapport dans `Outputs/`
3. Ouvrez le rapport Word généré
4. Vérifiez l'en-tête :
   - Le code contient-il la date d'exécution ?
   - Les champs sont-ils correctement remplis ?
   - L'hexagone a-t-il la bonne couleur selon le taux ?

### Dépannage

**Problème :** Les métadonnées ne sont pas utilisées

**Solutions :**
- Vérifiez que `__hyper_control_metadata__` est bien défini au niveau du module (pas dans une fonction)
- Vérifiez l'orthographe exacte de la variable (sensible à la casse)
- Vérifiez que tous les champs requis sont présents

---


**Date de création :** 5 décembre 2025  
**Version :** 1.0
