# Guide de Test - Graphiques Vega-Lite

## Checklist de Tests Manuels

### ✅ Test 1 : Vérification du Lancement
- [x] Le serveur démarre sans erreur
- [x] Le client démarre sans erreur
- [ ] Connexion possible avec un utilisateur

---

### ✅ Test 2 : Exécution d'une Analyse avec Graphiques

#### Étapes :
1. **Se connecter** avec un compte (ex: superadmin / password)
2. **Cliquer sur "Accueil"** dans le menu latéral
3. **Rechercher "Sauvegarde"** dans la barre de recherche
4. **Sélectionner** "Sauvegarde PCs" dans la liste
5. **Cliquer** sur "Lancer l'Analyse Sélectionnée"
6. **Saisir** une période (ex: "S04")
7. **Charger** les 3 fichiers requis :
   - OneDriveUsageAccountDetail (.csv)
   - Users (.csv)
   - Utilisateur AD (.txt)
8. **Cliquer** sur "Lancer l'Analyse"
9. **Attendre** la fin de l'exécution

#### Vérifications :
- [ ] L'analyse se termine sans erreur
- [ ] Les résultats s'affichent (tableau + statistiques)
- [ ] **Un bouton "📊 Voir les Graphiques" est visible**
- [ ] Les statistiques affichées sont :
  - [ ] Les utilisateurs actifs
  - [ ] Les utilisateurs Assujettis
  - [ ] Les utilisateurs avec licence
  - [ ] Les utilisateurs NOK
  - [ ] Taux

---

### ✅ Test 3 : Visualisation des Graphiques

#### Étapes :
1. **Cliquer** sur le bouton "📊 Voir les Graphiques"
2. **Attendre** l'ouverture du navigateur

#### Vérifications :
- [ ] Le navigateur s'ouvre automatiquement
- [ ] Une page HTML avec le titre "📊 Graphiques - Sauvegarde PCs" s'affiche
- [ ] **3 graphiques sont visibles** :

##### Graphique 1 : "Vue d'ensemble des utilisateurs" (Barres)
- [ ] Type : Barres verticales
- [ ] 3 barres visibles :
  - [ ] "Les utilisateurs actifs" (vert #4CAF50)
  - [ ] "Les utilisateurs Assujettis" (bleu #2196F3)
  - [ ] "Les utilisateurs avec licence" (orange #FF9800)
- [ ] Les valeurs correspondent aux statistiques affichées
- [ ] Au survol, un tooltip affiche la catégorie et la valeur

##### Graphique 2 : "Conformité des sauvegardes" (Circulaire)
- [ ] Type : Camembert
- [ ] 2 parts visibles :
  - [ ] "Les utilisateurs avec licence" (vert #4CAF50)
  - [ ] "Les utilisateurs NOK" (rouge #F44336)
- [ ] Les valeurs correspondent aux statistiques
- [ ] La légende est affichée sur le côté

##### Graphique 3 : "Taux de conformité" (Jauge)
- [ ] Type : Jauge circulaire
- [ ] La valeur du taux est affichée au centre (ex: "99.6%")
- [ ] La couleur de la jauge est :
  - [ ] Rouge si < 90%
  - [ ] Orange si 90-95%
  - [ ] Vert si > 95%
- [ ] Un arc gris représente la partie restante

---

### ✅ Test 4 : Interactivité des Graphiques

#### Pour chaque graphique :
- [ ] Au survol, les valeurs s'affichent dans un tooltip
- [ ] Un menu "..." apparaît en haut à droite
- [ ] Cliquer sur "..." → "Save as PNG" fonctionne
- [ ] Cliquer sur "..." → "View Source" affiche le code Vega-Lite

---

### ✅ Test 5 : Export Excel (Vérification que ça fonctionne toujours)

#### Étapes :
1. **Retourner** dans l'application Hyper-Framework
2. **Cliquer** sur "Exporter (Excel)"
3. **Choisir** un emplacement et sauvegarder

#### Vérifications :
- [ ] Le fichier Excel est créé
- [ ] Il contient les bonnes données
- [ ] L'export fonctionne toujours normalement

---

### ✅ Test 6 : Versioning avec Graphiques

#### Étapes :
1. **Cliquer** sur "Gestion Contrôles" dans le menu
2. **Sélectionner** "Sauvegarde PCs" dans la liste
3. **Cliquer** sur le bouton "Versioning"
4. **Vérifier** que l'analyse récente est listée
5. **Sélectionner** l'analyse dans la liste
6. **Cliquer** sur "Voir les Résultats"
7. **Attendre** l'affichage des détails

#### Vérifications :
- [ ] Les informations de l'analyse s'affichent (période, utilisateur, date)
- [ ] Les fichiers utilisés sont listés
- [ ] Les statistiques sont affichées
- [ ] **Le bouton "📊 Voir les Graphiques" est visible**
- [ ] Cliquer sur le bouton ouvre les graphiques dans le navigateur
- [ ] Les 3 graphiques s'affichent correctement

---

### ✅ Test 7 : Compatibilité avec Contrôles Sans Graphiques

#### Étapes :
1. **Lancer** un autre contrôle (ex: "Revue Intune")
2. **Charger** les fichiers requis
3. **Exécuter** l'analyse

#### Vérifications :
- [ ] L'analyse fonctionne normalement
- [ ] Les résultats s'affichent
- [ ] **Aucun bouton "📊 Voir les Graphiques" n'apparaît**
- [ ] L'export Excel fonctionne
- [ ] Pas d'erreur dans les logs

---

### ✅ Test 8 : Gestion d'Erreurs

#### Test 8.1 : Fichiers JSON existants
1. **Vérifier** le dossier `data/save/Sauvegarde PCs/Sauvegarde PCs S04/Outputs/`
2. **Ouvrir** le fichier JSON généré (ex: `results_20251123-XXXXXX.json`)
3. **Vérifier** que `chart_specs` est présent dans le JSON

#### Test 8.2 : Connexion Internet
1. **Désactiver** la connexion internet
2. **Cliquer** sur "📊 Voir les Graphiques"
3. **Vérifier** que les graphiques ne s'affichent pas (dépendance CDN)
4. **Réactiver** la connexion
5. **Réessayer** → Les graphiques doivent s'afficher

---

## Scénarios de Test Avancés

### 🔬 Test 9 : Modification de la Configuration

#### Étapes :
1. **Ouvrir** `hyper_framework_server/data/scripts/sauvegarde_pcs.py`
2. **Modifier** `__hyper_charts__` (ex: changer les couleurs)
3. **Enregistrer** et redémarrer l'application
4. **Re-lancer** une analyse
5. **Vérifier** que les changements sont appliqués

#### Exemple de modification :
```python
__hyper_charts__ = [
    {
        "type": "bar",
        "title": "NOUVEAU TITRE",
        "keys": ["Les utilisateurs actifs"],
        "colors": ["#9C27B0"],  # Violet
        "orientation": "horizontal"
    }
]
```

#### Vérifications :
- [ ] Le nouveau titre apparaît
- [ ] La couleur est violette
- [ ] Les barres sont horizontales

---

### 🔬 Test 10 : Ajout d'un Nouveau Type de Graphique

#### Étapes :
1. **Ajouter** un graphique de type "line" dans `__hyper_charts__`
2. **Relancer** l'analyse

#### Exemple :
```python
{
    "type": "line",
    "title": "Test ligne",
    "keys": ["Les utilisateurs actifs", "Les utilisateurs NOK"],
    "colors": ["#2196F3"]
}
```

#### Vérifications :
- [ ] Un 4ème graphique apparaît
- [ ] C'est un graphique en lignes
- [ ] Les points sont reliés

---

## Vérifications Techniques

### 📋 Logs du Serveur
**Vérifier dans le terminal du serveur** :
- [ ] Aucune erreur Python
- [ ] Aucune exception levée
- [ ] Les messages "Analyse en cours" s'affichent

### 📋 Structure des Fichiers
**Vérifier dans `data/save/`** :
```
Sauvegarde PCs/
  └── Sauvegarde PCs S04/
      ├── Inputs/
      │   ├── ad_file_*.txt
      │   ├── onedrive_file_*.csv
      │   └── users_file_*.csv
      └── Outputs/
          └── results_YYYYMMDD-HHMMSS.json  ← Doit contenir chart_specs
```

**Ouvrir le fichier JSON et vérifier** :
- [ ] Le champ `chart_specs` existe
- [ ] Il contient un tableau de 3 objets
- [ ] Chaque objet a une clé `$schema` avec "vega-lite"
- [ ] Chaque objet a un `title`, `data`, `mark`, `encoding`

---

## Problèmes Connus et Solutions

### ❌ Le bouton "📊 Voir les Graphiques" n'apparaît pas

**Causes possibles :**
1. La variable `__hyper_charts__` n'est pas définie
2. Le script a une erreur de syntaxe
3. Les `summary_stats` sont vides

**Solution :**
- Vérifier le fichier `sauvegarde_pcs.py`
- Regarder les logs du serveur pour détecter les erreurs

---

### ❌ Les graphiques sont vides ou incorrects

**Causes possibles :**
1. Les clés dans `keys` ne correspondent pas aux clés de `summary_stats`
2. Les valeurs sont `None` ou invalides

**Solution :**
- Ouvrir le fichier JSON dans `Outputs/`
- Comparer les clés de `summary_stats` avec celles de `chart_configs`
- Corriger les noms dans `__hyper_charts__`

---

### ❌ Erreur "Module not found: chart_generator"

**Cause :** Le fichier `chart_generator.py` n'est pas dans le bon dossier

**Solution :**
- Vérifier que `chart_generator.py` est dans `hyper_framework_server/services/`
- Redémarrer le serveur

---

### ❌ Les graphiques ne s'affichent pas (page blanche)

**Cause :** Pas de connexion internet (CDN Vega-Lite inaccessible)

**Solution :**
- Vérifier la connexion internet
- Vérifier dans la console du navigateur (F12) s'il y a des erreurs de chargement

---

## Résumé des Tests

| Test | Objectif | Statut |
|------|----------|--------|
| 1 | Lancement application | ✅ |
| 2 | Exécution analyse | ⏳ À tester |
| 3 | Visualisation graphiques | ⏳ À tester |
| 4 | Interactivité | ⏳ À tester |
| 5 | Export Excel | ⏳ À tester |
| 6 | Versioning | ⏳ À tester |
| 7 | Compatibilité | ⏳ À tester |
| 8 | Gestion erreurs | ⏳ À tester |

---

## Instructions de Test

1. **Suivre les tests dans l'ordre** (1 → 8)
2. **Cocher chaque case** au fur et à mesure
3. **Noter les problèmes** rencontrés
4. **Prendre des captures d'écran** des graphiques générés
5. **Vérifier les fichiers JSON** dans `Outputs/`

**Bon test ! 🧪**
