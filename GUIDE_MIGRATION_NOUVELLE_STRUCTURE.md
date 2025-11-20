# Guide de Migration - Nouvelle Structure de Stockage

## Vue d'ensemble

Cette mise à jour réorganise complètement la façon dont les fichiers d'analyse sont stockés sur le serveur pour une meilleure organisation et traçabilité.

### Ancienne Structure 

```
hyper_framework_server/
  └── data/
      ├── inputs/           # Tous les fichiers d'entrée mélangés
      │   ├── 20251120-083049_ad_file_ExtractionAD.txt
      │   ├── 20251120-083049_users_file_users.csv
      │   └── ...
      └── outputs/          # Tous les résultats mélangés
          └── ...
```

**Problèmes :**
- Tous les fichiers mélangés ensemble
- Difficile de retrouver les fichiers d'une analyse spécifique
- Pas de lien clair entre entrées et sorties
- Nécessite des timestamps dans les noms de fichiers

### Nouvelle Structure 

```
hyper_framework_server/
  └── data/
      └── save/
          └── [Nom du Contrôle]/
              └── [Nom du Contrôle] [Période]/
                  ├── Inputs/       # Fichiers d'entrée pour cette période
                  │   ├── ad_file_ExtractionAD.txt
                  │   ├── users_file_users.csv
                  │   └── onedrive_file_OneDrive.csv
                  └── Outputs/      # Résultats pour cette période
                      ├── results_20251120-083049.json
                      └── Rapport_Sauvegardes_PCs_S22_2025-11-20-08-30-49.docx
```

**Exemple concret :**

```
save/
  ├── Sauvegardes PCs/
  │   ├── Sauvegardes PCs S22/
  │   │   ├── Inputs/
  │   │   │   ├── ad_file_extraction.txt
  │   │   │   ├── users_file_users.csv
  │   │   │   └── onedrive_file_usage.csv
  │   │   └── Outputs/
  │   │       ├── results_20251120-083049.json
  │   │       └── Rapport_Sauvegardes_PCs_S22_2025-11-20-08-30-49.docx
  │   ├── Sauvegardes PCs S23/
  │   │   ├── Inputs/
  │   │   └── Outputs/
  │   └── Sauvegardes PCs S24/
  │       ├── Inputs/
  │       └── Outputs/
  │
  ├── Revue Intune/
  │   ├── Revue Intune S22/
  │   │   ├── Inputs/
  │   │   └── Outputs/
  │   └── Revue Intune S23/
  │       ├── Inputs/
  │       └── Outputs/
  │
  └── Analyse de Conformité des Serveurs/
      ├── Analyse de Conformité des Serveurs S22/
      │   ├── Inputs/
      │   └── Outputs/
      └── Analyse de Conformité des Serveurs S23/
          ├── Inputs/
          └── Outputs/
```

**Avantages :**
- ✅ Organisation claire par contrôle et période
- ✅ Facile de retrouver tous les fichiers d'une analyse
- ✅ Lien clair entre entrées et sorties
- ✅ Historique complet conservé par période
- ✅ Noms de fichiers plus simples (pas besoin de timestamp complexe)

## Fichiers Modifiés

### 1. Configuration (`config.py`)
- **SUPPRIMÉ** : `INPUTS_DIR`, `OUTPUTS_DIR`
- **AJOUTÉ** : `SAVE_DIR`

### 2. Routes d'Analyse (`api/analysis_routes.py`)
- Création automatique de la structure `save/[Contrôle]/[Contrôle Période]/Inputs|Outputs`
- Sauvegarde du JSON des résultats dans `Outputs/`
- Mise à jour du téléchargement de fichiers pour la nouvelle structure

### 3. Routes de Rapports (`api/report_routes.py`)
- Sauvegarde des rapports directement dans `Outputs/`
- Mise à jour du téléchargement pour supporter l'ancienne et la nouvelle structure

### 4. Service d'Exécution (`services/script_execution_engine.py`)
- Paramètre optionnel `inputs_dir_path` ajouté (pour compatibilité future)

## Procédure de Migration

### Étape 1 : Sauvegarder

**IMPORTANT** : Avant toute migration, sauvegardez votre dossier `data/` complet !

```powershell
# Dans le dossier hyper_framework_server/
Copy-Item -Path "data" -Destination "data_backup_$(Get-Date -Format 'yyyyMMdd')" -Recurse
```

### Étape 2 : Arrêter le Serveur

Arrêtez le serveur s'il est en cours d'exécution (Ctrl+C).

### Étape 3 : Exécuter la Migration

```powershell
cd hyper_framework_server/database
python migrate_to_new_structure.py
```

**Ce que fait le script :**
1. Vérifie si les anciens dossiers `inputs` et `outputs` existent
2. Crée le nouveau dossier `save/`
3. Renomme `inputs` → `inputs_OLD_BACKUP`
4. Renomme `outputs` → `outputs_OLD_BACKUP`

**Note** : Les anciens fichiers sont conservés dans les dossiers `_OLD_BACKUP` pour référence. La nouvelle structure se remplira automatiquement lors des prochaines analyses.

### Étape 4 : Redémarrer le Serveur

```powershell
cd ../..
python -m hyper_framework_server.run_server
```

### Étape 5 : Tester

1. Lancez le client et connectez-vous
2. Sélectionnez un contrôle (ex: "Sauvegardes PCs")
3. Lancez une analyse avec une période (ex: S22)
4. Vérifiez que la structure est créée :
   ```
   data/save/Sauvegardes PCs/Sauvegardes PCs S22/Inputs/
   data/save/Sauvegardes PCs/Sauvegardes PCs S22/Outputs/
   ```
5. Vérifiez que les fichiers sont bien sauvegardés dans ces dossiers

