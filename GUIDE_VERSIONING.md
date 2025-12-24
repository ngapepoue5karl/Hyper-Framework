# Guide du Versioning des Contrôles

## Vue d'Ensemble

Le **versioning** dans Hyper-Framework est un système automatique qui archive chaque exécution d'analyse. Il permet de :
- Consulter l'historique complet de toutes les analyses exécutées
- Retrouver les résultats d'analyses passées
- Télécharger les fichiers d'entrée et de sortie d'analyses précédentes
- Comparer les résultats entre différentes périodes
- Maintenir une traçabilité complète pour l'audit

---

## Comment Fonctionne le Versioning

### Sauvegarde Automatique

À **chaque exécution** d'un contrôle, le système enregistre automatiquement :

1. **Les métadonnées de l'exécution :**
   - Nom du contrôle
   - Type de périodicité (Semaine, Mois, Trimestre, Semestre)
   - Période concernée (ex: S22, M03, T2)
   - Utilisateur ayant lancé l'analyse
   - Date et heure d'exécution

2. **Les fichiers d'entrée :**
   - Tous les fichiers uploadés pour l'analyse
   - Conservés dans `data/[NomContrôle]/[Période]/Inputs/`

3. **Les résultats complets :**
   - DataFrame des résultats
   - Statistiques résumées
   - Configurations des graphiques
   - Fichier Excel généré
   - Rapport Word généré
   - Conservés dans `data/[NomContrôle]/[Période]/Outputs/`

### Organisation des Fichiers

```
data/
└── [Nom du Contrôle]/
    ├── S01/                          # Semaine 1
    │   ├── Inputs/
    │   │   ├── fichier1_20250115.csv
    │   │   └── fichier2_20250115.xlsx
    │   └── Outputs/
    │       ├── output_20250115_143025.xlsx
    │       ├── Rapport_S01_20250115_143025.docx
    │       └── results_20250115_143025.json
    ├── S02/                          # Semaine 2
    │   ├── Inputs/
    │   └── Outputs/
    └── M01/                          # Janvier
        ├── Inputs/
        └── Outputs/
```

### Base de Données

Chaque exécution crée une entrée dans la table `analysis_runs` :

```sql
CREATE TABLE analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id INTEGER NOT NULL,
    control_name TEXT NOT NULL,
    periodicity TEXT NOT NULL,          -- "WEEK", "MONTH", "QUARTER", "SEMESTER"
    period_label TEXT NOT NULL,         -- "S22", "M03", "T2", "SE1"
    username TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    results_json TEXT NOT NULL,         -- Résultats au format JSON
    files_info TEXT,                    -- Info sur les fichiers utilisés
    FOREIGN KEY (control_id) REFERENCES controls(id) ON DELETE CASCADE
);
```

---

## Accéder au Versioning

### Depuis l'Interface Client

**Méthode 1 : Menu Versioning Global**

1. Ouvrir l'application client Hyper-Framework
2. Se connecter avec vos identifiants
3. Dans le menu principal, cliquer sur **"Versioning"**
4. L'historique complet de **toutes** les analyses s'affiche

**Méthode 2 : Versioning d'un Contrôle Spécifique**

1. Aller dans **"Gestion des Contrôles"**
2. Sélectionner un contrôle dans la liste
3. Cliquer sur le bouton **"Voir Historique"**
4. L'historique filtré pour **ce contrôle uniquement** s'affiche

### Interface de Versioning

L'interface se divise en deux parties :

**Partie Supérieure : Liste des Analyses**

Tableau affichant :
- **Contrôle** : Nom du contrôle exécuté
- **Type** : Type de périodicité (Semaine, Mois, Trimestre, Semestre)
- **Période** : Label de la période (S22, M03, etc.)
- **Utilisateur** : Qui a lancé l'analyse
- **Date d'exécution** : Date et heure au format JJ/MM/AAAA HH:MM

**Partie Inférieure : Détails de l'Analyse**

Affiche les résultats complets de l'analyse sélectionnée :
- Statistiques résumées
- Graphiques interactifs
- Tableaux de données détaillées
- Liste des fichiers d'entrée utilisés

---

## Fonctionnalités Disponibles

### 1. Recherche et Filtrage

**Barre de recherche** en haut de la liste permet de filtrer par :
- Nom de contrôle
- Période (ex: "S22", "M03")
- Nom d'utilisateur

**Exemple :** Taper "sauvegarde" pour n'afficher que les analyses du contrôle de sauvegarde.

### 2. Voir les Résultats

**Bouton : "Voir les Résultats"**

1. Sélectionner une analyse dans la liste
2. Cliquer sur **"Voir les Résultats"**
3. Les détails s'affichent dans la partie inférieure :
   - Informations générales (contrôle, période, utilisateur, date)
   - Fichiers d'entrée utilisés
   - Statistiques clés
   - **Bouton " Voir les Graphiques"** (si graphiques disponibles)
   - Tableaux de données détaillées

**Graphiques Interactifs :**
- Cliquer sur " Voir les Graphiques" ouvre les graphiques dans le navigateur
- Graphiques Vega-Lite interactifs
- Possibilité d'exporter les graphiques en PNG

### 3. Exporter en Excel

**Bouton : "Exporter (Excel)"**

1. Sélectionner une analyse dans la liste
2. Cliquer sur **"Exporter (Excel)"**
3. Choisir l'emplacement et le nom du fichier
4. Le fichier Excel est créé avec toutes les données

**Format du fichier exporté :**
- Une feuille par section de résultats
- Colonnes avec les labels définis dans le script
- Nom par défaut : `Resultats_[NomControle]_[Periode]_[DateHeure].xlsx`

**Exemple :** `Resultats_Sauvegarde_PCs_S22_2025-01-15-14-30-25.xlsx`

### 4. Télécharger le Dossier Complet

**Bouton : "Télécharger Dossier Complet"**

Cette fonctionnalité télécharge **tout le dossier** de l'analyse sous forme de ZIP :

1. Sélectionner une analyse dans la liste
2. Cliquer sur **"Télécharger Dossier Complet"**
3. Choisir un dossier de destination
4. Le système crée un dossier `[NomControle] [Periode]` contenant :
   - **Inputs/** : Tous les fichiers d'entrée utilisés
   - **Outputs/** : Tous les fichiers générés (Excel, Word, JSON)

**Exemple de contenu téléchargé :**

```
Sauvegarde des PCs S22/
├── Inputs/
│   ├── OneDriveUsageAccountDetail_20250115.csv
│   ├── Users_20250115.csv
│   └── Utilisateur_AD_20250115.txt
└── Outputs/
    ├── output_20250115_143025.xlsx
    ├── Rapport_S22_20250115_143025.docx
    └── results_20250115_143025.json
```

**Cas d'usage :**
- Archivage complet d'une analyse
- Partage avec un collègue
- Réutilisation des fichiers d'entrée pour une nouvelle analyse
- Vérification approfondie des données

---

## Gestion des Périodes

### Types de Périodicité

Hyper-Framework supporte 4 types de périodicité :

| Type | Valeur | Format du Label | Exemple | Description |
|------|--------|-----------------|---------|-------------|
| **Semaine** | `WEEK` | `SXX` | `S22` | Semaine 22 de l'année |
| **Mois** | `MONTH` | `MXX` | `M03` | Mars (mois 3) |
| **Trimestre** | `QUARTER` | `TX` | `T2` | Trimestre 2 |
| **Semestre** | `SEMESTER` | `SEX` | `SE1` | Semestre 1 |

### Définir la Périodicité d'un Contrôle

Dans votre script, utilisez la variable `__hyper_periodicity__` :

```python
# Contrôle hebdomadaire
__hyper_periodicity__ = 'WEEK'

# Contrôle mensuel
__hyper_periodicity__ = 'MONTH'

# Contrôle trimestriel
__hyper_periodicity__ = 'QUARTER'

# Contrôle semestriel
__hyper_periodicity__ = 'SEMESTER'
```

### Sélection de la Période lors de l'Exécution

Lors du lancement d'une analyse, l'utilisateur doit sélectionner la période :

**Pour un contrôle hebdomadaire :**
- Liste déroulante : `S01`, `S02`, ..., `S52`

**Pour un contrôle mensuel :**
- Liste déroulante : `M01` (Janvier), `M02` (Février), ..., `M12` (Décembre)

**Pour un contrôle trimestriel :**
- Liste déroulante : `T1`, `T2`, `T3`, `T4`

**Pour un contrôle semestriel :**
- Liste déroulante : `SE1`, `SE2`

---

## Scénarios d'Utilisation

### Scénario 1 : Comparer les Résultats sur Plusieurs Semaines

**Objectif :** Voir l'évolution du taux de conformité d'un contrôle hebdomadaire

**Étapes :**

1. Aller dans **Versioning**
2. Rechercher le nom du contrôle (ex: "conformité terminaux")
3. Sélectionner l'analyse de la semaine S20 → Voir les résultats → Noter le taux
4. Sélectionner l'analyse de la semaine S21 → Voir les résultats → Noter le taux
5. Sélectionner l'analyse de la semaine S22 → Voir les résultats → Noter le taux
6. Comparer les taux pour identifier les tendances

**Astuce :** Utiliser "Exporter (Excel)" pour chaque semaine et consolider dans un tableau de suivi.

### Scénario 2 : Retrouver les Fichiers d'Entrée d'une Analyse Passée

**Objectif :** Réutiliser les fichiers d'une analyse précédente

**Étapes :**

1. Aller dans **Versioning**
2. Rechercher et sélectionner l'analyse souhaitée
3. Cliquer sur **"Télécharger Dossier Complet"**
4. Choisir un dossier de destination
5. Ouvrir le dossier → Dossier **Inputs/** contient tous les fichiers

**Utilisation :**
- Vérifier les données sources utilisées
- Comparer avec de nouvelles données
- Re-exécuter une analyse avec les mêmes fichiers

### Scénario 3 : Partager les Résultats d'une Analyse avec un Collègue

**Objectif :** Envoyer le rapport et les données à un collègue

**Méthode 1 : Export Excel uniquement**

1. Sélectionner l'analyse
2. Cliquer sur **"Exporter (Excel)"**
3. Envoyer le fichier Excel par email

**Méthode 2 : Dossier complet**

1. Sélectionner l'analyse
2. Cliquer sur **"Télécharger Dossier Complet"**
3. Compresser le dossier en ZIP
4. Envoyer le ZIP contenant inputs, outputs et rapport

### Scénario 4 : Vérifier Qui a Exécuté une Analyse

**Objectif :** Traçabilité et audit

**Étapes :**

1. Aller dans **Versioning**
2. Rechercher par période ou nom de contrôle
3. La colonne **"Utilisateur"** indique qui a lancé l'analyse
4. La colonne **"Date d'exécution"** indique quand

**Utilisation :**
- Audit de conformité
- Validation des processus
- Suivi des responsabilités

### Scénario 5 : Consulter un Rapport Word Généré il y a 3 Mois

**Objectif :** Retrouver un rapport archivé

**Étapes :**

1. Aller dans **Versioning**
2. Rechercher le contrôle et la période (ex: "M09" pour septembre)
3. Sélectionner l'analyse
4. Cliquer sur **"Télécharger Dossier Complet"**
5. Ouvrir le dossier → Dossier **Outputs/** → Fichier `.docx`

**Alternative :** Si le serveur est accessible, naviguer directement vers :
```
hyper_framework_server/data/[NomControle]/[Periode]/Outputs/
```

---

## Limitations et Bonnes Pratiques

### Limitations

**1. Pas de Modification des Résultats Passés**

Les résultats dans le versioning sont **en lecture seule**. On ne peut pas :
- Modifier les statistiques d'une analyse passée
- Supprimer une analyse individuelle
- Éditer les fichiers archivés

**Solution :** Pour corriger des résultats, re-exécuter une nouvelle analyse avec les bonnes données.

**2. Pas de Comparaison Automatique**

L'interface ne propose pas encore de vue comparative automatique entre deux périodes.

**Solution :** Exporter les résultats en Excel et créer manuellement les comparaisons.

**3. Limite de Stockage**

Chaque analyse consomme de l'espace disque (fichiers + base de données).

**Solution :** Archiver périodiquement les anciennes analyses sur un support externe.

### Bonnes Pratiques

**1. Nommer les Fichiers de Manière Cohérente**

Lors de l'upload, utiliser des noms de fichiers clairs :

 **Bon :**
- `OneDriveUsage_2025-01-15.csv`
- `Users_Janvier2025.csv`

 **Mauvais :**
- `data.csv`
- `fichier1.xlsx`
- `nouveau.txt`

**2. Documenter les Analyses Spéciales**

Si une analyse a été exécutée dans des conditions particulières, le noter dans :
- Un fichier texte dans les Inputs
- Les recommandations du rapport Word

**3. Archiver Régulièrement**

**Recommandation :** Une fois par trimestre :

1. Télécharger les dossiers complets des analyses importantes
2. Sauvegarder sur un support externe ou cloud
3. Vérifier l'intégrité des archives

**4. Nettoyer l'Historique Ancien**

Pour les contrôles très fréquents, considérer :
- Conserver 1 an d'historique dans le système
- Archiver les données plus anciennes hors du serveur
- Documenter la procédure d'archivage

**5. Utiliser le Versioning pour la Formation**

Les nouvelles personnes peuvent :
- Consulter des analyses passées comme exemples
- Comprendre les tendances historiques
- Apprendre les bonnes pratiques

**6. Vérifier la Cohérence des Périodes**

S'assurer que la période sélectionnée correspond bien aux fichiers uploadés :

**Cohérent :**
- Période : `S22` (semaine 22)
- Fichiers : Données de la semaine du 27 mai au 2 juin

**Incohérent :**
- Période : `S22`
- Fichiers : Données de la semaine du 15 au 21 juin (semaine 24)

---

## Sécurité et Permissions

### Qui Peut Accéder au Versioning ?

**Tous les utilisateurs authentifiés** peuvent accéder au versioning, mais avec des restrictions :

| Rôle | Permissions |
|------|-------------|
| **VIEWER** | Voir toutes les analyses, exporter Excel, télécharger dossiers |
| **AUDITOR** | Idem VIEWER |
| **SUPER_ADMIN** | Accès complet, peut aussi supprimer des contrôles (supprime l'historique associé) |

### Téléchargement des Fichiers d'Entrée

**Important :** Les fichiers d'entrée peuvent contenir des données sensibles.

**Règle :** Seuls les utilisateurs ayant le droit peuvent télécharger le dossier complet.

**Vérification :** Le serveur vérifie les permissions avant chaque téléchargement.

### Traçabilité

Toutes les actions sur le versioning sont **loggées** :

- `VIEW_ANALYSIS_RUNS` : Consultation de la liste
- `VIEW_ANALYSIS_RUN_DETAILS` : Consultation d'une analyse
- `DOWNLOAD_CONTROL_FOLDER` : Téléchargement d'un dossier

**Consultation des logs :** Accessible via l'interface dans le menu "Logs" (SUPER_ADMIN).

---

## Maintenance et Administration

### Nettoyer les Anciennes Analyses

**Pour les administrateurs système :**

**Option 1 : Suppression d'un Contrôle Complet**

1. Aller dans **Gestion des Contrôles**
2. Sélectionner le contrôle à supprimer
3. Cliquer sur **"Supprimer"**
4. **Conséquence :** Toutes les analyses associées sont supprimées (CASCADE)

**Option 2 : Suppression Manuelle dans la Base de Données**

```sql
-- Supprimer les analyses avant une certaine date
DELETE FROM analysis_runs 
WHERE executed_at < '2024-01-01';

-- Supprimer les analyses d'un contrôle spécifique
DELETE FROM analysis_runs 
WHERE control_id = 5;
```

**Attention :** Supprimer les fichiers associés manuellement dans `data/[NomControle]/`.

### Sauvegarde de la Base de Données

**Recommandation :** Sauvegarder régulièrement `hyper_framework_server.db`

**Commande PowerShell :**

```powershell
# Copier la base de données
Copy-Item "hyper_framework_server/data/hyper_framework_server.db" `
          "backups/hyper_framework_server_$(Get-Date -Format 'yyyyMMdd').db"
```

**Automatisation :** Créer une tâche planifiée hebdomadaire.

### Optimiser la Base de Données

Après de nombreuses analyses, optimiser la base SQLite :

```sql
-- Réorganiser et optimiser
VACUUM;

-- Analyser pour les statistiques de requête
ANALYZE;
```

**Exécution :**

```powershell
# Depuis le dossier du serveur
sqlite3 data/hyper_framework_server.db "VACUUM; ANALYZE;"
```

---

## Dépannage

### L'historique est vide

**Causes possibles :**
1. Aucune analyse n'a encore été exécutée
2. Problème de connexion au serveur
3. Base de données corrompue

**Solutions :**
- Vérifier que des analyses ont bien été lancées
- Vérifier la connexion réseau au serveur
- Consulter les logs du serveur
- Vérifier l'intégrité de la base de données

### "Analyse non trouvée" lors de la consultation

**Cause :** L'analyse a été supprimée de la base de données

**Solution :** 
- Vérifier si le contrôle parent a été supprimé
- Restaurer depuis une sauvegarde si nécessaire

### Le téléchargement du dossier échoue

**Causes possibles :**
1. Fichiers manquants sur le serveur
2. Problème de permissions sur le dossier `data/`
3. Chemin de fichier trop long (limite Windows : 260 caractères)

**Solutions :**
- Vérifier l'existence du dossier sur le serveur
- Vérifier les permissions du dossier `data/`
- Choisir un chemin de destination plus court
- Consulter les logs du serveur pour plus de détails

### Les graphiques ne s'affichent pas

**Cause :** Les `chart_specs` n'ont pas été sauvegardés ou sont invalides

**Solutions :**
- Vérifier que le script définit bien `__hyper_charts__`
- Re-exécuter l'analyse avec la configuration correcte
- Consulter GUIDE_GRAPHIQUES_VEGALITE.md

### Erreur lors de l'export Excel

**Causes possibles :**
1. Pandas non installé sur le client
2. Données invalides dans `results_json`
3. Nom de fichier avec caractères interdits

**Solutions :**
- Installer pandas : `pip install pandas openpyxl`
- Vérifier les logs d'erreur
- Choisir un nom de fichier simple (pas de caractères spéciaux)

---

## API REST pour le Versioning

Pour les développeurs souhaitant intégrer le versioning dans d'autres outils :

### Récupérer la Liste des Analyses

```http
GET /analysis-runs?username=johndoe
```

**Réponse :**
```json
[
  {
    "id": 42,
    "control_id": 5,
    "control_name": "Sauvegarde des PCs",
    "periodicity": "WEEK",
    "period_label": "S22",
    "username": "johndoe",
    "executed_at": "2025-01-15T14:30:25Z"
  },
  ...
]
```

### Récupérer les Détails d'une Analyse

```http
GET /analysis-runs/42?username=johndoe
```

**Réponse :**
```json
{
  "id": 42,
  "control_id": 5,
  "control_name": "Sauvegarde des PCs",
  "periodicity": "WEEK",
  "period_label": "S22",
  "username": "johndoe",
  "executed_at": "2025-01-15T14:30:25Z",
  "results_json": [...],
  "files_info": [...]
}
```

### Télécharger le Dossier Complet

```http
GET /analysis-runs/42/download-folder?username=johndoe
```

**Réponse :** Fichier ZIP contenant Inputs/ et Outputs/

---

## Évolutions Futures

**Fonctionnalités prévues :**

- **Comparaison automatique** entre deux périodes
- **Export multi-périodes** en un seul fichier Excel avec plusieurs onglets
- **Graphiques de tendance** affichant l'évolution des KPIs sur plusieurs périodes
- **Annotations** pour documenter des analyses spécifiques
- **Filtres avancés** (par plage de dates, par taux de conformité, etc.)
- **Dashboard de synthèse** avec vue d'ensemble de tous les contrôles

---

## Références

- **Gestion des contrôles :** Voir README.md
- **Métadonnées du contrôle :** Voir [GUIDE_METADONNEES_CONTROLE.md](GUIDE_METADONNEES_CONTROLE.md)
- **Configuration des graphiques :** Voir [GUIDE_GRAPHIQUES_VEGALITE.md](GUIDE_GRAPHIQUES_VEGALITE.md)
- **Génération des rapports :** Voir [GUIDE_GENERATION_RAPPORTS.md](GUIDE_GENERATION_RAPPORTS.md)

---

**Date de création :** 27 Novembre 2025  
**Version :** 1.0  
**Auteur :** Karl Popper
