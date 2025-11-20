# Liste des Fichiers Modifiés - Nouvelle Structure de Stockage

##  Vue d'Ensemble

Cette mise à jour réorganise complètement le système de stockage des fichiers pour une meilleure organisation par contrôle et période.

---

##  Fichiers Modifiés

### 1. Configuration

#### `hyper_framework_server/config.py`
**Modifications :**
- Suppression des variables `_INPUTS_DIR`, `_OUTPUTS_DIR`, `INPUTS_DIR`, `OUTPUTS_DIR`
- Ajout de `_SAVE_DIR` et `SAVE_DIR`
- Mise à jour de la liste `dirs_to_create`

**Impact :** Toutes les références à `INPUTS_DIR` et `OUTPUTS_DIR` ont été remplacées par une logique basée sur `SAVE_DIR`

---

### 2. API Routes

#### `hyper_framework_server/api/analysis_routes.py`
**Modifications :**

1. **Route `/controls/<int:control_id>/execute`** 
   - Création de la structure `save/[Contrôle]/[Contrôle Période]/Inputs|Outputs/`
   - Sauvegarde des fichiers dans le dossier `Inputs/` correspondant
   - Sauvegarde du JSON des résultats dans `Outputs/results_*.json`
   - Ajout du chemin relatif dans `files_info`

2. **Route `/results/<path:filepath>`** 
   - Support des chemins relatifs depuis `save/`
   - Vérification de sécurité pour empêcher l'accès en dehors de `save/`

3. **Route `/analysis-runs/<int:run_id>/download-files`** 
   - Mise à jour pour chercher les fichiers dans la nouvelle structure
   - Utilisation de `relative_path` depuis `files_info`
   - Fallback pour les anciens enregistrements

**Impact :** Toutes les exécutions d'analyses utilisent maintenant la nouvelle structure

---

#### `hyper_framework_server/api/report_routes.py`
**Modifications :**

1. **Route `/execute-and-generate`** 
   - Ajout du paramètre `period_label`
   - Création de la structure de dossiers comme dans `analysis_routes.py`
   - Sauvegarde des fichiers d'entrée dans `Inputs/`
   - Sauvegarde du rapport DOCX dans `Outputs/`

2. **Route `/download/<path:filepath>`** 
   - Support des chemins relatifs depuis `save/`
   - Recherche d'abord dans la nouvelle structure
   - Fallback vers l'ancien dossier `reports/` pour compatibilité

**Impact :** Les rapports générés sont maintenant sauvegardés dans la structure hiérarchique

---

### 3. Services

#### `hyper_framework_server/services/script_execution_engine.py`
**Modifications :**
- Ajout d'un paramètre optionnel `inputs_dir_path` à la fonction `execute_script_from_file`

**Impact :** Compatibilité future si besoin de passer le chemin des inputs au script

---

##  Nouveaux Fichiers Créés

### 1. Scripts de Migration

#### `hyper_framework_server/database/migrate_to_new_structure.py`
**Fonction :** Script de migration pour :
- Créer le dossier `save/`
- Renommer `inputs/` → `inputs_OLD_BACKUP/`
- Renommer `outputs/` → `outputs_OLD_BACKUP/`
- Préserver les anciens fichiers

**Utilisation :**
```powershell
cd hyper_framework_server/database
python migrate_to_new_structure.py
```

---

#### `hyper_framework_server/database/test_new_structure.py`
**Fonction :** Script de test pour :
- Vérifier que `SAVE_DIR` existe
- Créer une structure de test
- Valider l'écriture de fichiers
- Afficher l'arborescence

**Utilisation :**
```powershell
cd hyper_framework_server/database
python test_new_structure.py
```
