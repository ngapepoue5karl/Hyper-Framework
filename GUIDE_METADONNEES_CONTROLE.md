# Guide des Métadonnées de Contrôle

## Vue d'Ensemble

Ce guide explique comment définir les métadonnées d'un contrôle pour personnaliser l'en-tête des rapports générés automatiquement.

---

## Structure des Métadonnées

Chaque script de contrôle doit définir une variable `__hyper_control_metadata__` contenant un dictionnaire avec les champs suivants :

```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_XX_XXX",     # Préfixe du code (la date sera ajoutée automatiquement)
    "application": "Nom des applications",       # Applications concernées (séparées par des virgules)
    "layer": "Couche",                          # Couche concernée (Physique, Données, Application, etc.)
    "risk_reference": "R123, R456",             # Références des risques (séparées par des virgules)
    "risk_name": "Nom du risque",               # Nom du risque (peut être multiligne avec \n)
    "control_name": "Nom du contrôle",          # Nom complet du contrôle
    "ref_description": "CTL_SSI_XXX_XXX_X",     # Référence de description
    "description": "Description du contrôle",   # Description détaillée du contrôle
    "analyse": "Points d'analyse du contrôle"   # Liste des points d'analyse (peut être multiligne)
}
```

---

## Champs Détaillés

### 1. `control_code_prefix`
**Format :** `CTL_SSI_XX_XXX`

Le code unique du contrôle **sans la date**. La date d'exécution sera ajoutée automatiquement au format `YYYY_MM_DD`.

**Exemple :**
- Défini : `"CTL_SSI_02_SAVE"`
- Résultat dans le rapport : `CTL_SSI_02_SAVE_2025_12_02` (si exécuté le 2 décembre 2025)

### 2. `application`
**Format :** Texte libre, applications séparées par des virgules

Les applications ou systèmes concernés par le contrôle.

**Exemples :**
- `"OneDrive"`
- `"CrowdStrike, Tanium, AD"`
- `"CrowdStrike, Tanium, AD, GLPI, Intune"`

### 3. `layer`
**Format :** Texte libre

La couche du système d'information concernée.

**Exemples courants :**
- `"Données"`
- `"Physique"`
- `"Application"`
- `"Réseau"`

### 4. `risk_reference`
**Format :** `RXX, RYY` (références séparées par des virgules)

Les références des risques couverts par le contrôle.

**Exemples :**
- `"R182, R211"`
- `"R24"`
- `"R45, R67, R89"`

### 5. `risk_name`
**Format :** Texte libre (supporte le multiligne avec `\n`)

Le nom ou la description du risque. Peut contenir plusieurs lignes.

**Exemples :**
- `"Absence de contrôle efficace de modification de configuration"`
- `"Indisponibilité du système d'information\nPerte des données"` (2 lignes)

### 6. `control_name`
**Format :** Texte libre

Le nom complet et descriptif du contrôle.

**Exemples :**
- `"Sauvegarde des données des PCs"`
- `"Conformité des terminaux"`
- `"Conformité des serveurs"`

### 7. `ref_description`
**Format :** `CTL_SSI_XXX_XXX_X`

La référence de description du contrôle (différente du code).

**Exemples :**
- `"CTL_SSI_DON_SAVE_2"`
- `"CTL_SSI_PHY_TMO_1"`
- `"CTL_SSI_PHY_SRV_1"`

### 8. `description`
**Format :** Texte libre

La description détaillée du contrôle expliquant son objectif.

**Exemples :**
- `"Vérifier que la synchronisation des données des utilisateurs de SABC est activée sur OneDrive."`
- `"Ce contrôle a pour but d'assurer le suivi de la conformité des terminaux mis à la disposition du personnel du Groupe SABC."`
- `"Ce contrôle a pour but d'assurer le suivi de la conformité des serveurs du Groupe SABC."`

### 9. `analyse`
**Format :** Texte libre (supporte le multiligne avec `\n` ou triple quotes)

La liste des points d'analyse effectués par le contrôle. Pour les listes à puces, utiliser le caractère `•`.

**Exemples :**
- Simple : `"Ressortir les utilisateurs dont les données n'ont pas été synchronisées sur OneDrive au cours des 30 derniers jours."`
- Multiligne :
```python
"""• Ressortir les équipements Windows non-conformes sur Intune ;
• Ressortir les équipements de l'AD qui ne sont pas enrôlés sur Intune ;
• Ressortir les ordinateurs personnels qui sont enrôlés sur Intune."""
```

---

## Exemples Complets

### Exemple 1 : Sauvegarde des PCs

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

### Exemple 2 : Conformité des Terminaux

```python
# analyse_de_conformité_des_terminaux.py

__hyper_inputs__ = [
    {"key": "adws_file", "label": "Fichier ADWS - Export Active Directory", "format": "csv"},
    {"key": "glpi_file", "label": "Fichier GLPI - Inventaire", "format": "csv"},
    # ... autres inputs ...
]

__hyper_periodicity__ = 'WEEK'

__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_01_TMO",
    "application": "CrowdStrike, Tanium, AD, GLPI, Intune",
    "layer": "Physique",
    "risk_reference": "R24",
    "risk_name": "Absence de contrôle efficace de modification de configuration",
    "control_name": "Conformité des terminaux",
    "ref_description": "CTL_SSI_PHY_TMO_1",
    "description": "Ce contrôle a pour but d'assurer le suivi de la conformité des terminaux mis à la disposition du personnel du Groupe SABC.",
    "analyse": """• Ressortir les équipements Windows non-conformes sur Intune (compliance ≠ compliant) ;
• Ressortir les équipements de l'AD qui ne sont pas enrôlés sur Intune ;
• Ressortir les ordinateurs personnels qui sont enrôlés sur Intune ;
• Ressortir les équipements de l'AD qui n'apparaissent pas sur CrowdStrike ;
• Ressortir les équipements de l'AD qui n'apparaissent pas sur Tanium ;
• Ressortir les équipements de l'AD qui ne remontent pas LAPS ;
• Ressortir les équipements de l'AD dont la version de Windows < 10.0 (19045)."""
}

# ... reste du script ...
```

### Exemple 3 : Conformité des Serveurs

```python
# analyse_de_conformité_des_serveurs.py

__hyper_inputs__ = [
    {"key": "ad_data", "label": "Extraction des serveurs AD (.csv)", "format": "csv"},
    {"key": "cs_data", "label": "Rapport de l'agent CrowdStrike (.csv)", "format": "csv"},
    # ... autres inputs ...
]

__hyper_periodicity__ = 'WEEK'

__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_01_SRV",
    "application": "CrowdStrike, Tanium, AD",
    "layer": "Physique",
    "risk_reference": "R24",
    "risk_name": "Absence de contrôle efficace de modification de configuration",
    "control_name": "Conformité des serveurs",
    "ref_description": "CTL_SSI_PHY_SRV_1",
    "description": "Ce contrôle a pour but d'assurer le suivi de la conformité des serveurs du Groupe SABC.",
    "analyse": """• Ressortir les serveurs de l'AD qui n'apparaissent pas sur CrowdStrike ;
• Ressortir les serveurs de l'AD qui n'apparaissent pas sur Tanium ;
• Ressortir les serveurs de l'AD dont l'OS est antérieur à Windows Server 2016."""
}

# ... reste du script ...
```

---

## Indicateur de Conclusion (Hexagone)

L'hexagone de conclusion est **généré automatiquement** en fonction du taux de conformité calculé dans les statistiques du contrôle.

### Règles de Couleur

| Taux de Conformité | Couleur    | Code Hex  |
|-------------------|-----------|-----------|
| 95% - 100%        | 🟢 Vert    | #4CAF50   |
| 50% - 94%         | 🟡 Jaune   | #FFC107   |
| 0% - 49%          | 🔴 Rouge   | #F44336   |

### Comment le Taux est Calculé

Le système cherche automatiquement dans `summary_stats` une clé contenant :
- `"taux"`
- `"conformité"` ou `"conformite"`

**Exemples de clés détectées :**
- `"Taux de conformité"` ✅
- `"Taux"` ✅
- `"Pourcentage de conformité"` ✅
- `"Rate"` ❌ (ne contient pas les mots-clés)

**Format de la valeur :**
- `"99.63%"` ✅ (string avec %)
- `99.63` ✅ (nombre)
- `"99,63%"` ⚠️ (fonctionne mais préférer le point)

---

## Placement dans le Script

Les métadonnées doivent être placées **au début du fichier**, juste après les autres variables spéciales :

```python
# 1. Définition des inputs
__hyper_inputs__ = [...]

# 2. Périodicité (optionnel)
__hyper_periodicity__ = 'WEEK'

# 3. Configuration des graphiques (optionnel)
__hyper_charts__ = [...]

# 4. ✨ MÉTADONNÉES DU CONTRÔLE (NOUVEAU)
__hyper_control_metadata__ = {
    "control_code_prefix": "...",
    "application": "...",
    # ... autres champs ...
}

# 5. Imports et reste du code
import pandas as pd
# ...
```

---

## Résultat dans le Rapport

Les métadonnées remplissent automatiquement l'en-tête du rapport généré :

```
┌──────────────────────────────────────────────────────────┐
│ [LOGO]  │  Nom du Contrôle (centré)  │  CTL_SSI_XX_YYYY_MM_DD │
├──────────────────────────────────────────────────────────┤
│ Application │ Couche   │ Ref Risque │ Nom Risque │ 🔶 │ Nom Contrôle │
│ concernée   │ concernée│            │            │    │              │
├──────────────────────────────────────────────────────────┤
│ Destinataire: ... │ Ref Description: CTL_SSI_XXX_XXX_X │ PS3... │
└──────────────────────────────────────────────────────────┘
```

---

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

✅ **Solutions :**
- Vérifiez que `__hyper_control_metadata__` est bien défini au niveau du module (pas dans une fonction)
- Vérifiez l'orthographe exacte de la variable (sensible à la casse)
- Vérifiez que tous les champs requis sont présents

**Problème :** L'hexagone ne change pas de couleur

✅ **Solutions :**
- Vérifiez que votre script retourne bien un `summary_stats` contenant un taux
- Vérifiez que la clé contient "taux", "conformité" ou "conformite"
- Vérifiez que la valeur est un nombre ou une string avec %

**Problème :** La date dans le code est incorrecte

✅ **Solutions :**
- La date est automatique, basée sur l'heure d'exécution du contrôle
- Si nécessaire, vérifiez que `execution_date` est bien passé dans `analysis_routes.py`

---

## Migration de Scripts Existants

Pour migrer un script existant :

1. **Ouvrez le fichier du script** dans `hyper_framework_server/data/scripts/`

2. **Ajoutez le bloc de métadonnées** après `__hyper_periodicity__` :

```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_XX_XXX",  # À définir
    "application": "...",                      # À définir
    "layer": "...",                           # À définir
    "risk_reference": "...",                  # À définir
    "risk_name": "...",                       # À définir
    "control_name": "...",                    # À définir
    "ref_description": "..."                  # À définir
}
```

3. **Remplissez chaque champ** selon votre contrôle

4. **Testez** en exécutant le contrôle et en vérifiant le rapport généré

---

## Bonnes Pratiques

### ✅ À FAIRE

- Définir toutes les métadonnées au début du fichier
- Utiliser des codes de contrôle cohérents avec la nomenclature
- Documenter les risques de manière claire et concise
- Tester le rapport généré après ajout des métadonnées

### ❌ À ÉVITER

- Ne pas définir de métadonnées (valeurs par défaut = "N/A")
- Utiliser des codes de contrôle incohérents
- Oublier de mettre à jour les métadonnées lors de modifications du contrôle
- Utiliser des caractères spéciaux qui pourraient causer des problèmes (emojis, etc.)

---

## Support et Questions

Pour toute question sur la définition des métadonnées :

1. Consultez les exemples dans les scripts existants
2. Vérifiez ce guide pour les formats requis
3. Testez avec un rapport de test pour valider le résultat

---

**Date de création :** 2 décembre 2025  
**Version :** 1.0
