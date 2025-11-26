# Guide d'Utilisation des Graphiques Vega-Lite

## Introduction

Ce guide explique comment ajouter facilement des graphiques interactifs à vos scripts de contrôle dans Hyper-Framework. Les graphiques sont générés automatiquement à partir des statistiques de résumé (`summary_stats`) que votre script retourne.

## Principe de Fonctionnement

1. **Votre script** définit une variable `__hyper_charts__` qui configure les graphiques souhaités
2. **Le framework** lit automatiquement cette configuration lors de l'exécution
3. **Les graphiques** sont générés à partir des `summary_stats` de vos résultats
4. **L'utilisateur** peut cliquer sur " Voir les Graphiques" pour les visualiser dans son navigateur

## Types de Graphiques Disponibles

### 1. Graphique en Barres (`bar`)
Idéal pour comparer plusieurs valeurs côte à côte.

### 2. Graphique Circulaire (`pie`)
Parfait pour montrer des proportions ou répartitions.

### 3. Jauge / Indicateur (`gauge`)
Excellent pour afficher un taux ou pourcentage avec seuils de couleur.

### 4. Graphique en Lignes (`line`)
Utile pour montrer des tendances (évolutions futures).

---

## Guide Pas-à-Pas : Ajouter des Graphiques

### Étape 1 : Définir `__hyper_charts__` dans votre script

Ajoutez cette section **au début de votre fichier**, juste après `__hyper_inputs__` et `__hyper_periodicity__` :

```python
# Configuration des graphiques à afficher
__hyper_charts__ = [
    {
        "type": "bar",
        "title": "Mon premier graphique",
        "keys": ["Statistique 1", "Statistique 2", "Statistique 3"],
        "colors": ["#4CAF50", "#2196F3", "#FF9800"],
        "orientation": "vertical"  # ou "horizontal"
    }
]
```

### Étape 2 : S'assurer que vos `summary_stats` contiennent les bonnes clés

Les clés dans `"keys"` doivent **exactement correspondre** aux clés de votre dictionnaire `summary_stats`.

Exemple dans votre fonction `run()` :

```python
def run(input_file_paths: dict, output_dir_path: str):
    # ... votre traitement ...
    
    return [{
        "title": "Résultats de l'analyse",
        "dataframe": df_results,
        "display_columns": [...],
        "summary_stats": {
            "Statistique 1": 100,
            "Statistique 2": 250,
            "Statistique 3": 175
        }
    }]
```

### Étape 3 : Tester !

1. Lancez votre analyse dans Hyper-Framework
2. Un bouton " Voir les Graphiques" apparaîtra automatiquement
3. Cliquez dessus pour voir vos graphiques dans le navigateur

---

## Exemples Complets

### Exemple 1 : Graphique en Barres Simple

```python
__hyper_charts__ = [
    {
        "type": "bar",
        "title": "Nombre d'utilisateurs par catégorie",
        "keys": ["Utilisateurs actifs", "Utilisateurs inactifs", "Utilisateurs suspendus"],
        "colors": ["#4CAF50", "#FFC107", "#F44336"],
        "orientation": "vertical"
    }
]

# Dans votre fonction run() :
return [{
    "title": "Analyse des utilisateurs",
    "dataframe": df,
    "display_columns": [...],
    "summary_stats": {
        "Utilisateurs actifs": 1523,
        "Utilisateurs inactifs": 234,
        "Utilisateurs suspendus": 12
    }
}]
```

### Exemple 2 : Graphique Circulaire (Conformité)

```python
__hyper_charts__ = [
    {
        "type": "pie",
        "title": "Répartition Conformité vs Non-Conformité",
        "keys": ["Conforme", "Non conforme"],
        "colors": ["#4CAF50", "#F44336"]
    }
]

# Dans votre fonction run() :
return [{
    "title": "Conformité des équipements",
    "dataframe": df,
    "display_columns": [...],
    "summary_stats": {
        "Conforme": 487,
        "Non conforme": 13
    }
}]
```

### Exemple 3 : Jauge avec Taux

```python
__hyper_charts__ = [
    {
        "type": "gauge",
        "title": "Taux de conformité",
        "key": "Taux",  # Notez : "key" au singulier pour la jauge
        "max_value": 100,
        "colors": ["#F44336", "#FF9800", "#4CAF50"],  # Rouge, Orange, Vert
        "thresholds": [85, 95]  # <85% rouge, 85-95% orange, >95% vert
    }
]

# Dans votre fonction run() :
return [{
    "title": "Résultats de conformité",
    "dataframe": df,
    "display_columns": [...],
    "summary_stats": {
        "Total équipements": 500,
        "Équipements conformes": 487,
        "Équipements NOK": 13,
        "Taux": "97.4%"  # Peut être un string avec % ou un nombre
    }
}]
```

### Exemple 4 : Plusieurs Graphiques

Vous pouvez combiner plusieurs graphiques en ajoutant plusieurs dictionnaires dans la liste :

```python
__hyper_charts__ = [
    {
        "type": "bar",
        "title": "Vue d'ensemble",
        "keys": ["Total", "Traités", "En attente"],
        "colors": ["#9E9E9E", "#4CAF50", "#FFC107"]
    },
    {
        "type": "pie",
        "title": "Répartition par statut",
        "keys": ["Validé", "En cours", "Rejeté"],
        "colors": ["#4CAF50", "#2196F3", "#F44336"]
    },
    {
        "type": "gauge",
        "title": "Taux de validation",
        "key": "Taux de validation",
        "max_value": 100,
        "thresholds": [70, 90]
    }
]
```

---

## Exemple Réel : Script `sauvegarde_pcs.py`

Voici comment le script `sauvegarde_pcs.py` utilise les graphiques :

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

# Et dans la fonction run() :
return [{
    "title": "Sauvegardes des données PCs",
    "excel_output": out_xlsx,
    "dataframe": dataframe_for_ui(view),
    "display_columns": [{"key": c, "label": c} for c in view.columns],
    "summary_stats": {
        "Les utilisateurs actifs": 3046,
        "Les utilisateurs Assujettis": 2581,
        "Les utilisateurs avec licence": 2445,
        "Les utilisateurs NOK": 9,
        "Taux": "99.63%"
    }
}]
```

---

## Configuration Détaillée des Graphiques

### Graphique en Barres

```python
{
    "type": "bar",
    "title": "Titre du graphique",
    "keys": ["Clé1", "Clé2", "Clé3"],           # Obligatoire
    "colors": ["#couleur1", "#couleur2", ...],   # Optionnel
    "orientation": "vertical" ou "horizontal"    # Optionnel, défaut: "vertical"
}
```

### Graphique Circulaire

```python
{
    "type": "pie",
    "title": "Titre du graphique",
    "keys": ["Clé1", "Clé2"],                    # Obligatoire
    "colors": ["#couleur1", "#couleur2"]         # Optionnel
}
```

### Jauge

```python
{
    "type": "gauge",
    "title": "Titre du graphique",
    "key": "Clé unique",                         # Obligatoire (singulier!)
    "max_value": 100,                            # Optionnel, défaut: 100
    "colors": ["#rouge", "#orange", "#vert"],    # Optionnel
    "thresholds": [50, 80]                       # Optionnel, défaut: [50, 80]
}
```

**Note sur les thresholds** : 
- Valeur < threshold[0] → couleur 1 (rouge)
- threshold[0] ≤ valeur < threshold[1] → couleur 2 (orange)
- valeur ≥ threshold[1] → couleur 3 (vert)

---

## Codes Couleur Recommandés

### Couleurs de Base
- Vert (succès) : `#4CAF50`
- Bleu (info) : `#2196F3`
- Orange (warning) : `#FF9800` ou `#FFC107`
- Rouge (erreur) : `#F44336`
- Gris : `#9E9E9E`
- Violet : `#9C27B0`

### Pour la Conformité
- Conforme : `#4CAF50` (vert)
- Non conforme : `#F44336` (rouge)

### Pour les Jauges (ordre Rouge→Orange→Vert)
```python
"colors": ["#F44336", "#FF9800", "#4CAF50"]
```

---

## Dépannage

### Le bouton " Voir les Graphiques" n'apparaît pas

**Causes possibles :**
1. La variable `__hyper_charts__` n'est pas définie dans votre script
2. Votre script a une erreur de syntaxe
3. Les `summary_stats` sont vides

**Solution :** Vérifiez que `__hyper_charts__` est bien défini au début du fichier.

### Les graphiques sont vides ou affichent une erreur

**Causes possibles :**
1. Les `keys` dans `__hyper_charts__` ne correspondent pas exactement aux clés de `summary_stats`
2. Les valeurs dans `summary_stats` sont `None` ou invalides

**Solution :** 
- Assurez-vous que les noms de clés correspondent **exactement** (respectez la casse et les espaces)
- Vérifiez que les valeurs sont des nombres ou des strings avec `%`

### Les valeurs avec `%` ne s'affichent pas correctement

**Solution :** Le framework gère automatiquement les strings avec `%`. Exemple :
```python
"Taux": "99.63%"  # ✅ Fonctionne
"Taux": 99.63     # ✅ Fonctionne aussi
```

### Je veux plus de contrôle sur les graphiques

Pour des graphiques plus complexes, vous pouvez :
1. Consulter la documentation Vega-Lite : https://vega.github.io/vega-lite/
2. Modifier le fichier `hyper_framework_server/services/chart_generator.py`
3. Créer de nouveaux types de graphiques personnalisés

---

## Checklist pour Ajouter des Graphiques

- [ ] Définir `__hyper_charts__` au début du script
- [ ] Vérifier que les `keys` correspondent exactement aux clés de `summary_stats`
- [ ] Choisir des couleurs appropriées
- [ ] Tester localement l'exécution du contrôle
- [ ] Vérifier que le bouton "📊 Voir les Graphiques" apparaît
- [ ] Cliquer sur le bouton pour voir les graphiques
- [ ] Vérifier que les graphiques sont corrects et lisibles

---

## Bonnes Pratiques

1. **Nommage des clés** : Utilisez des noms explicites et cohérents
2. **Limitation** : Ne créez pas plus de 5 graphiques par contrôle
3. **Couleurs** : Respectez les conventions (vert = bien, rouge = problème)
4. **Types de graphiques** : 
   - Barres → Comparaisons
   - Circulaire → Proportions/Répartitions
   - Jauge → Taux/Pourcentages
5. **Ordre des graphiques** : Mettez le plus important en premier

---

## Support et Aide

Si vous avez des questions ou besoin d'aide :
1. Consultez les exemples dans `sauvegarde_pcs.py`
2. Regardez le code de `chart_generator.py` pour comprendre les possibilités
3. Testez avec des données simples d'abord

**Bon développement ! 📊**
