# Modifications du Bouton Versioning

## Résumé des Changements

Le bouton **"Versioning"** a été déplacé de la barre de navigation latérale vers l'onglet **"Gestion Contrôles"**. 

Maintenant, pour voir l'historique des analyses d'un contrôle spécifique :
1. Cliquez sur **"Gestion Contrôles"** dans le menu latéral
2. Sélectionnez un contrôle dans la liste
3. Cliquez sur le bouton **"Versioning"** (situé après le bouton "Voir")
4. L'interface affichera uniquement les analyses exécutées pour ce contrôle

## Fichiers Modifiés

### 1. `hyper_framework_client/ui/main_window.py`
- ✅ Suppression du bouton "Versioning" de la barre de navigation latérale
- ✅ Suppression de la méthode `show_versioning_frame()`
- ✅ Ajustement des positions des boutons restants (row 1, 2, 3, 4)
- ✅ Ajout de la méthode `open_versioning(control_id, control_name)` pour ouvrir le versioning filtré

### 2. `hyper_framework_client/ui/control_management_window.py`
- ✅ Ajout du bouton "Versioning" dans le frame d'actions (après le bouton "Voir")
- ✅ Le bouton est désactivé par défaut et s'active lors de la sélection d'un contrôle
- ✅ Ajout du binding `<<TreeviewSelect>>` pour gérer l'état du bouton
- ✅ Ajout de la méthode `on_tree_selection_change()` pour activer/désactiver le bouton
- ✅ Ajout de la méthode `show_versioning_for_control()` pour ouvrir le versioning filtré

### 3. `hyper_framework_client/ui/versioning_frame.py`
- ✅ Modification du constructeur pour accepter les paramètres `control_id` et `control_name`
- ✅ Ajout des attributs `self.filter_control_id` et `self.filter_control_name`
- ✅ Titre dynamique qui affiche le nom du contrôle si un filtrage est actif
- ✅ Modification de la méthode `filter_runs()` pour filtrer par `control_id` si fourni

## Nouveau Flux d'Utilisation

### Avant (Ancien comportement)
```
Menu latéral → Versioning → Liste de TOUTES les analyses → Voir les résultats
```

### Maintenant (Nouveau comportement)
```
Menu latéral → Gestion Contrôles → Sélectionner un contrôle → 
Bouton "Versioning" → Liste des analyses DE CE CONTRÔLE → Voir les résultats
```

## Avantages

1. **Contexte clair** : L'utilisateur voit directement l'historique du contrôle qui l'intéresse
2. **Navigation logique** : Le versioning est lié à la gestion des contrôles
3. **Interface épurée** : Un bouton de moins dans la barre de navigation
4. **Filtrage automatique** : Plus besoin de chercher dans une longue liste

## Tests à Effectuer

✅ **Test 1 : Vérifier que le bouton apparaît**
- Ouvrir "Gestion Contrôles"
- Vérifier que le bouton "Versioning" est présent (désactivé)

✅ **Test 2 : Vérifier l'activation du bouton**
- Sélectionner un contrôle dans la liste
- Le bouton "Versioning" devrait s'activer

✅ **Test 3 : Vérifier le filtrage**
- Cliquer sur "Versioning"
- Vérifier que seules les analyses du contrôle sélectionné s'affichent
- Vérifier que le titre affiche le nom du contrôle

✅ **Test 4 : Vérifier la fonctionnalité complète**
- Sélectionner une analyse dans la liste filtrée
- Cliquer sur "Voir les Résultats"
- Vérifier que les résultats s'affichent correctement
- Tester l'export Excel

✅ **Test 5 : Vérifier la recherche**
- Dans le versioning filtré, utiliser la barre de recherche
- Vérifier que la recherche fonctionne uniquement sur les analyses du contrôle

## Notes Importantes

- ⚠️ **Aucune modification côté serveur** : L'API retourne déjà le `control_id` dans les données
- ✅ **Rétrocompatibilité** : Si `control_id` est None, le versioning affiche toutes les analyses
- 🔒 **Permissions** : Le bouton Versioning est visible pour tous les utilisateurs ayant accès à "Gestion Contrôles"

## En Cas de Problème

Si le bouton "Versioning" n'apparaît pas :
1. Vérifier que l'utilisateur a la permission `VIEW_CONTROLS`
2. Vérifier que le fichier `control_management_window.py` a bien été modifié
3. Redémarrer l'application client

Si le filtrage ne fonctionne pas :
1. Vérifier que le serveur retourne bien le champ `control_id` dans `/api/analysis-runs`
2. Vérifier les logs du serveur pour détecter d'éventuelles erreurs
3. Vérifier que la base de données contient bien la colonne `control_id` dans la table `analysis_runs`

---

**Date de modification** : 10 novembre 2025
**Version** : 2.1
