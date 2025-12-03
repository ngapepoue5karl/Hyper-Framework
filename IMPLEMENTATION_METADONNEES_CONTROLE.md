# Implémentation des Métadonnées de Contrôle Dynamiques

## Résumé des Modifications

Date : 2 décembre 2025  
Version : 1.0

---

## Objectif

Permettre à chaque script de contrôle de définir ses propres métadonnées qui seront utilisées pour remplir dynamiquement l'en-tête des rapports Word générés automatiquement.

---

## Fichiers Modifiés

### 1. Scripts de Contrôle
Ajout de la variable `__hyper_control_metadata__` dans chaque script :

#### ✅ `sauvegarde_pcs.py`
```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_02_SAVE",
    "application": "OneDrive",
    "layer": "Données",
    "risk_reference": "R182, R211",
    "risk_name": "Indisponibilité du système d'information\nPerte des données",
    "control_name": "Sauvegarde des données des PCs",
    "ref_description": "CTL_SSI_DON_SAVE_2"
}
```

#### ✅ `analyse_de_conformité_des_terminaux.py`
```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_01_TMO",
    "application": "CrowdStrike, Tanium, AD, GLPI, Intune",
    "layer": "Physique",
    "risk_reference": "R24",
    "risk_name": "Absence de contrôle efficace de modification de configuration",
    "control_name": "Conformité des terminaux",
    "ref_description": "CTL_SSI_PHY_TMO_1"
}
```

#### ✅ `analyse_de_conformité_des_serveurs.py`
```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_01_SRV",
    "application": "CrowdStrike, Tanium, AD",
    "layer": "Physique",
    "risk_reference": "R24",
    "risk_name": "Absence de contrôle efficace de modification de configuration",
    "control_name": "Conformité des serveurs",
    "ref_description": "CTL_SSI_PHY_SRV_1"
}
```

#### ✅ `revue_intune.py`
```python
__hyper_control_metadata__ = {
    "control_code_prefix": "CTL_SSI_03_INT",
    "application": "Intune, AD, GLPI",
    "layer": "Physique",
    "risk_reference": "R25",
    "risk_name": "Utilisation non autorisée des équipements",
    "control_name": "Revue des équipements multiples par utilisateur",
    "ref_description": "CTL_SSI_PHY_INT_1"
}
```

---

### 2. `script_execution_engine.py`

**Modifications :**
- Extraction des métadonnées depuis `__hyper_control_metadata__`
- Retour d'un tuple `(results, control_metadata)` au lieu de seulement `results`

**Code ajouté :**
```python
# Extraire les métadonnées du contrôle si elles existent
control_metadata = None
if hasattr(analysis_module, '__hyper_control_metadata__'):
    control_metadata = getattr(analysis_module, '__hyper_control_metadata__')

return results, control_metadata
```

---

### 3. `analysis_routes.py`

**Modifications :**
- Réception des métadonnées depuis `script_execution_engine`
- Passage des métadonnées et de la date d'exécution au générateur de rapport

**Code modifié :**
```python
# Ligne 165 : Récupération des métadonnées
results_with_dfs, control_metadata = execute_script_from_file(script_path, input_file_paths, outputs_dir)

# Ligne ~250 : Passage au générateur de rapport
report_service.generate_and_save_report(
    user_data={'username': username},
    control_data={'name': control_name},
    analysis_results=serialized_results,
    save_path=report_path,
    period_label=period_label,
    control_metadata=control_metadata,      # 🆕 NOUVEAU
    execution_date=run_timestamp            # 🆕 NOUVEAU
)
```

---

### 4. `report_service.py`

**Modifications majeures :**

#### A. Nouvelle Fonction : `_create_conclusion_hexagon()`
Génère un hexagone coloré selon le taux de conformité :
- 🟢 Vert (95-100%)
- 🟡 Jaune (50-94%)
- 🔴 Rouge (0-49%)

```python
def _create_conclusion_hexagon(self, compliance_rate):
    """Crée un hexagone coloré selon le taux de conformité."""
    if compliance_rate >= 95:
        color = '#4CAF50'  # Vert
    elif compliance_rate >= 50:
        color = '#FFC107'  # Jaune/Orange
    else:
        color = '#F44336'  # Rouge
    
    # Création avec matplotlib.patches.RegularPolygon
    # ... (voir code source pour détails)
    
    return temp_file.name
```

#### B. Modification : `_add_header_with_logo_and_table()`
Utilisation des métadonnées pour remplir dynamiquement le tableau d'en-tête :

**Nouveaux paramètres :**
```python
def _add_header_with_logo_and_table(
    self, 
    document, 
    control_name, 
    control_code, 
    analysis_results,
    control_metadata=None,      # 🆕 NOUVEAU
    execution_date=None         # 🆕 NOUVEAU
):
```

**Changements clés :**

1. **Code de contrôle dynamique avec date :**
```python
# Avant :
code_run = code_para.add_run(control_code)

# Après :
if control_metadata and execution_date:
    control_code_prefix = control_metadata.get('control_code_prefix', control_code)
    date_part = execution_date.split('-')[0]  # YYYYMMDD
    formatted_date = f"{date_part[:4]}_{date_part[4:6]}_{date_part[6:8]}"
    full_control_code = f"{control_code_prefix}_{formatted_date}"
else:
    full_control_code = control_code
```

2. **Remplissage du tableau depuis les métadonnées :**
```python
if control_metadata:
    application = control_metadata.get('application', 'N/A')
    layer = control_metadata.get('layer', 'N/A')
    risk_reference = control_metadata.get('risk_reference', 'N/A')
    risk_name = control_metadata.get('risk_name', 'N/A')
    control_name_meta = control_metadata.get('control_name', control_name)
else:
    # Valeurs par défaut si pas de métadonnées
    application = 'N/A'
    # ...
```

3. **Calcul automatique du taux de conformité :**
```python
compliance_rate = 0
if analysis_results and len(analysis_results) > 0:
    first_section = analysis_results[0]
    summary_stats = first_section.get('summary_stats', {})
    
    # Chercher le taux dans les statistiques
    for key, value in summary_stats.items():
        if 'taux' in key.lower() or 'conformité' in key.lower():
            # Extraction du nombre
            if isinstance(value, str):
                match = re.search(r'(\d+\.?\d*)', value)
                if match:
                    compliance_rate = float(match.group(1))
```

4. **Insertion de l'hexagone dans la cellule "Conclusion" :**
```python
# Colonne 4 (index 4) = Conclusion avec hexagone
if i == 4:
    try:
        hexagon_path = self._create_conclusion_hexagon(compliance_rate)
        cell_run = cell_para.add_run()
        cell_run.add_picture(hexagon_path, width=Inches(0.25))
        cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Nettoyer le fichier temporaire
        os.unlink(hexagon_path)
    except Exception as e:
        # Fallback: afficher le taux en texte
        cell_run = cell_para.add_run(f"{compliance_rate:.1f}%")
```

5. **Référence description dynamique :**
```python
# Avant :
ref_run2 = ref_para.add_run('CTL_SSI_DON_SAVE_2')

# Après :
ref_description = 'N/A'
if control_metadata:
    ref_description = control_metadata.get('ref_description', 'N/A')
ref_run2 = ref_para.add_run(ref_description)
```

#### C. Modification : `generate_and_save_report()`
Ajout de paramètres et passage aux fonctions :

```python
def generate_and_save_report(
    self, 
    user_data, 
    control_data, 
    analysis_results, 
    save_path, 
    period_label='N/A',
    control_metadata=None,      # 🆕 NOUVEAU
    execution_date=None         # 🆕 NOUVEAU
):
    # ...
    self._add_header_with_logo_and_table(
        document, 
        control_name, 
        control_code, 
        analysis_results,
        control_metadata=control_metadata,      # 🆕 NOUVEAU
        execution_date=execution_date           # 🆕 NOUVEAU
    )
```

---

## Fonctionnalités Ajoutées

### 1. Code de Contrôle Dynamique
Le code inclut maintenant automatiquement la date d'exécution :
- Format : `{prefix}_{YYYY}_{MM}_{DD}`
- Exemple : `CTL_SSI_02_SAVE_2025_12_02`

### 2. Tableau d'En-tête Personnalisé
Chaque contrôle définit ses propres informations :
- Application concernée
- Couche concernée
- Référence du risque
- Nom du risque (supporte multiligne)
- Nom du contrôle
- Référence description

### 3. Indicateur Visuel de Conformité (Hexagone)
Un hexagone coloré remplace le texte dans la colonne "Conclusion" :
- 🟢 Vert : Taux ≥ 95%
- 🟡 Jaune : Taux 50-94%
- 🔴 Rouge : Taux < 50%

### 4. Calcul Automatique du Taux
Le système détecte automatiquement le taux de conformité dans les statistiques en cherchant les clés contenant :
- "taux"
- "conformité" ou "conformite"

---

## Workflow Complet

```
1. Utilisateur exécute un contrôle
   ↓
2. script_execution_engine.py charge le script
   ├─ Extraction de __hyper_control_metadata__
   └─ Retour (results, control_metadata)
   ↓
3. analysis_routes.py reçoit les métadonnées
   ├─ Capture de la date d'exécution (run_timestamp)
   └─ Passage à report_service.generate_and_save_report()
   ↓
4. report_service.py génère le rapport
   ├─ Utilisation des métadonnées pour l'en-tête
   ├─ Calcul du taux de conformité
   ├─ Génération de l'hexagone coloré
   ├─ Construction du code avec date
   └─ Sauvegarde du rapport Word
   ↓
5. Rapport finalisé avec en-tête personnalisé
```

---

## Compatibilité

### Scripts avec Métadonnées ✅
Les scripts définissant `__hyper_control_metadata__` bénéficient de toutes les fonctionnalités :
- En-tête personnalisé
- Code avec date dynamique
- Hexagone de conclusion
- Tous les champs remplis

### Scripts sans Métadonnées ⚠️
Les scripts existants **continuent de fonctionner** avec des valeurs par défaut :
- Champs remplis avec "N/A"
- Hexagone basé sur le taux détecté (si disponible)
- Code de contrôle fixe (sans date)

**Aucune rupture de compatibilité !**

---

## Tests Requis

### Tests Fonctionnels
1. ✅ Exécution de `sauvegarde_pcs.py`
   - Vérifier le code : `CTL_SSI_02_SAVE_YYYY_MM_DD`
   - Vérifier application : "OneDrive"
   - Vérifier hexagone selon le taux

2. ✅ Exécution de `analyse_de_conformité_des_terminaux.py`
   - Vérifier le code : `CTL_SSI_01_TMO_YYYY_MM_DD`
   - Vérifier applications multiples
   - Vérifier référence : `CTL_SSI_PHY_TMO_1`

3. ✅ Exécution de `analyse_de_conformité_des_serveurs.py`
   - Vérifier le code : `CTL_SSI_01_SRV_YYYY_MM_DD`
   - Vérifier référence : `CTL_SSI_PHY_SRV_1`

4. ✅ Exécution de `revue_intune.py`
   - Vérifier le code : `CTL_SSI_03_INT_YYYY_MM_DD`
   - Vérifier référence : `CTL_SSI_PHY_INT_1`

### Tests de Régression
- Exécuter un ancien script sans métadonnées
- Vérifier que le rapport se génère toujours
- Vérifier les valeurs par défaut ("N/A")

---

## Documentation

### Nouveaux Fichiers
1. **`GUIDE_METADONNEES_CONTROLE.md`**
   - Guide complet pour définir les métadonnées
   - Exemples pour chaque champ
   - Bonnes pratiques
   - Dépannage

2. **`IMPLEMENTATION_METADONNEES_CONTROLE.md`** (ce fichier)
   - Résumé technique des modifications
   - Liste des fichiers modifiés
   - Workflow détaillé

---

## Migration Future

Pour ajouter des métadonnées à de nouveaux contrôles :

1. Ouvrir le script dans `hyper_framework_server/data/scripts/`
2. Ajouter `__hyper_control_metadata__` après `__hyper_periodicity__`
3. Remplir les 7 champs requis
4. Tester l'exécution et le rapport généré

**Référence :** Voir `GUIDE_METADONNEES_CONTROLE.md`

---

## Maintenance

### Points d'Attention
- Les métadonnées sont extraites à chaque exécution (pas de cache)
- L'hexagone est généré à la volée et nettoyé automatiquement
- Le taux de conformité est détecté automatiquement dans les statistiques

### Évolutions Possibles
- [ ] Validation des métadonnées au chargement du script
- [ ] Interface UI pour éditer les métadonnées
- [ ] Support de métadonnées dans un fichier externe (JSON/YAML)
- [ ] Ajout de champs supplémentaires (propriétaire, date de création, etc.)

---

**Auteur :** GitHub Copilot  
**Date :** 2 décembre 2025  
**Version :** 1.0
