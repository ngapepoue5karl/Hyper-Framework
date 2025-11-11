# Guide de Déploiement - Nouvelles Fonctionnalités

## Étapes pour Déployer les Nouvelles Fonctionnalités

### 1. Mise à jour du Serveur

#### Option A : Nouvelle Installation
Si vous installez le serveur pour la première fois :
1. Les nouvelles modifications sont déjà incluses
2. La table `analysis_runs` sera créée automatiquement lors de la première exécution

#### Option B : Mise à jour d'un Serveur Existant

**Étape 1 : Arrêter le serveur**
```bash
# Arrêter le processus du serveur en cours
# (Ctrl+C si lancé en mode console)
```

**Étape 2 : Sauvegarder la base de données**
```bash
cd hyper_framework_server/data
copy hyper_framework_server.db hyper_framework_server.db.backup
```

**Étape 3 : Remplacer les fichiers du serveur**
- Remplacez le dossier `hyper_framework_server` complet par la nouvelle version
- OU remplacez uniquement les fichiers modifiés :
  - `database/schema.sql`
  - `api/analysis_routes.py`
  - Ajoutez `database/migrate_add_analysis_runs.py` (nouveau)

**Étape 4 : Exécuter la migration de la base de données**
```bash
cd hyper_framework_server/database
python migrate_add_analysis_runs.py
```

Vous devriez voir :
```
✓ Migration réussie ! La table 'analysis_runs' a été créée.
```

**Étape 5 : Redémarrer le serveur**
```bash
cd ../..
python -m hyper_framework_server.run_server
```

### 2. Mise à jour du Client

#### Option A : Nouvelle Installation
Si vous créez un nouvel installateur :
1. Les nouvelles modifications sont déjà incluses
2. Suivez le processus normal de création de l'installateur avec PyInstaller et Inno Setup

#### Option B : Mise à jour des Clients Existants

**Méthode 1 : Réinstallation complète (Recommandé)**
1. Créez un nouvel installateur avec les nouvelles modifications
2. Distribuez-le aux utilisateurs
3. Les utilisateurs exécutent le nouvel installateur qui remplacera l'ancienne version

**Méthode 2 : Remplacement manuel (Pour tests)**
1. Fermez l'application cliente si elle est ouverte
2. Remplacez les fichiers modifiés dans le dossier d'installation :
   - `ui/main_window.py`
   - `ui/analysis_selection_frame.py`
   - `ui/generic_analysis_window.py`
   - Ajoutez `ui/versioning_frame.py` (nouveau)
   - Ajoutez `ui/dialogs.py` (nouveau)
   - `api/api_client.py`

### 3. Vérification du Déploiement

#### Vérifications Serveur

**1. Vérifier que la table est créée**
```bash
cd hyper_framework_server/data
sqlite3 hyper_framework_server.db
```

Dans SQLite :
```sql
.tables
-- Vous devriez voir : analysis_runs  controls  users

.schema analysis_runs
-- Devrait afficher la structure de la table

.exit
```

**2. Vérifier les logs du serveur**
Lancez le serveur et vérifiez qu'il démarre sans erreur.

**3. Tester l'API**
Vous pouvez utiliser curl ou Postman pour tester les nouveaux endpoints :
```bash
# Liste des analyses (remplacez localhost par l'IP du serveur si nécessaire)
curl "http://localhost:5000/api/analysis-runs?username=superadmin"
```

#### Vérifications Client

**1. Vérifier l'interface**
- Lancez le client
- Connectez-vous
- Vérifiez que le bouton "Versioning" apparaît sous "Accueil"

**2. Test du flux complet**
1. Cliquez sur "Accueil"
2. Sélectionnez un contrôle
3. Cliquez sur "Lancer l'Analyse Sélectionnée"
4. Vérifiez que la fenêtre de saisie de semaine s'affiche
5. Saisissez "S45" (par exemple)
6. Vérifiez que la fenêtre d'analyse s'ouvre avec "📅 Semaine : S45" affiché
7. Chargez les fichiers et lancez l'analyse
8. Après l'analyse, allez dans "Versioning"
9. Vérifiez que l'analyse apparaît dans la liste
10. Sélectionnez-la et cliquez sur "Voir les Résultats"
11. Vérifiez que les résultats s'affichent correctement

### 4. En Cas de Problème

#### Le serveur ne démarre pas après la migration

**Solution** :
1. Vérifiez les logs d'erreur
2. Restaurez la sauvegarde de la base de données
```bash
cd hyper_framework_server/data
copy hyper_framework_server.db.backup hyper_framework_server.db
```
3. Réexécutez la migration

#### Le client affiche une erreur au lancement d'une analyse

**Symptôme** : Erreur "missing 1 required positional argument: 'week_label'"

**Solution** :
- Vérifiez que TOUS les fichiers modifiés ont été remplacés
- En particulier `main_window.py`, `analysis_selection_frame.py` et `dialogs.py`

#### La section Versioning est vide ou affiche une erreur

**Vérifications** :
1. Le serveur a-t-il été mis à jour avec les nouveaux endpoints ?
2. La table `analysis_runs` existe-t-elle dans la base ?
3. Y a-t-il des analyses déjà exécutées depuis la mise à jour ?

**Note** : Les analyses exécutées AVANT la mise à jour ne seront pas dans l'historique.

#### Erreur "table analysis_runs already exists"

**Explication** : Normal si vous réexécutez le script de migration

**Solution** : Aucune action nécessaire, le script détecte la table existante

### 5. Rollback (Retour en Arrière)

Si vous devez annuler la mise à jour :

**Serveur** :
1. Arrêtez le serveur
2. Restaurez l'ancienne version des fichiers
3. Restaurez la sauvegarde de la base de données
```bash
cd hyper_framework_server/data
copy hyper_framework_server.db.backup hyper_framework_server.db
```

**Client** :
1. Réinstallez l'ancienne version du client
2. OU restaurez manuellement les anciens fichiers

**Note** : Les données de la table `analysis_runs` seront perdues lors du rollback si vous restaurez la base de données.

### 6. Checklist de Déploiement

Avant de déployer en production :

- [ ] Sauvegarde de la base de données serveur effectuée
- [ ] Migration de la base de données testée en environnement de test
- [ ] Nouveau client testé en environnement de test
- [ ] Flux complet testé (saisie semaine → analyse → versioning)
- [ ] Documentation mise à jour et distribuée aux utilisateurs
- [ ] Support/helpdesk informé des nouvelles fonctionnalités
- [ ] Plan de rollback préparé et testé

### 7. Communication aux Utilisateurs

**Email type à envoyer** :

```
Objet : Nouvelle version Hyper-Framework - Fonctionnalité Versioning

Bonjour,

Une nouvelle version de Hyper-Framework est disponible avec les améliorations suivantes :

1. Saisie de la semaine : Vous devrez maintenant indiquer la semaine lors du lancement d'une analyse (ex: S22)

2. Section Versioning : Un nouvel onglet "Versioning" vous permet de consulter l'historique complet de toutes les analyses exécutées et de réexporter les résultats.

Mise à jour :
- Le serveur sera redémarré le [DATE] à [HEURE]
- Veuillez installer la nouvelle version du client en exécutant Setup_HyperFramework_Client_vX.X.exe

Documentation complète : Voir NOUVELLES_FONCTIONNALITES.md

Support : [CONTACT]

Cordialement,
```

### 8. Monitoring Post-Déploiement

**Pendant les premiers jours** :
- Surveillez les logs du serveur pour détecter les erreurs
- Collectez les retours des utilisateurs
- Vérifiez que la table `analysis_runs` se remplit correctement
- Surveillez la taille de la base de données

**Métriques à surveiller** :
- Nombre d'analyses dans `analysis_runs`
- Taille du fichier `hyper_framework_server.db`
- Temps de réponse de l'endpoint `/api/analysis-runs`
- Utilisation de la fonctionnalité Versioning dans les logs

### 9. Maintenance Future

#### Purge de l'historique (optionnel)
Pour supprimer les analyses de plus de X mois :

```sql
DELETE FROM analysis_runs 
WHERE executed_at < datetime('now', '-6 months');
```

#### Optimisation des Performances
Si vous avez beaucoup d'analyses (>1000), vous pouvez ajouter des index :

```sql
CREATE INDEX idx_analysis_runs_week ON analysis_runs(week_label);
CREATE INDEX idx_analysis_runs_user ON analysis_runs(username);
CREATE INDEX idx_analysis_runs_date ON analysis_runs(executed_at);
```

#### Sauvegarde
N'oubliez pas d'inclure la table `analysis_runs` dans vos sauvegardes régulières.

---

**Version** : 2.0
**Date** : Novembre 2025
