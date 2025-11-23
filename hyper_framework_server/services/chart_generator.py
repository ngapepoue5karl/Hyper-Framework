"""
Module de génération de graphiques Vega-Lite à partir des statistiques de contrôles.

Ce module facilite la création de visualisations pour les scripts de contrôle
en générant automatiquement des spécifications Vega-Lite à partir des données.
"""

import json
from typing import Dict, List, Any, Optional


def generate_chart_specs(
    summary_stats: Dict[str, Any],
    chart_configs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Génère des spécifications Vega-Lite pour les graphiques.
    
    Args:
        summary_stats: Dictionnaire de statistiques (ex: {"Les utilisateurs actifs": 3046, ...})
        chart_configs: Liste de configurations de graphiques définies dans le script de contrôle
        
    Returns:
        Liste de spécifications Vega-Lite prêtes à être affichées
        
    Exemple d'utilisation dans un script de contrôle:
        chart_configs = [
            {
                "type": "bar",
                "title": "Statistiques des utilisateurs",
                "keys": ["Les utilisateurs actifs", "Les utilisateurs Assujettis", "Les utilisateurs avec licence"],
                "colors": ["#4CAF50", "#2196F3", "#FF9800"]
            },
            {
                "type": "pie",
                "title": "Conformité des sauvegardes",
                "keys": ["Les utilisateurs avec licence", "Les utilisateurs NOK"],
                "colors": ["#4CAF50", "#F44336"]
            }
        ]
    """
    specs = []
    
    for config in chart_configs:
        chart_type = config.get("type", "bar")
        
        if chart_type == "bar":
            spec = _generate_bar_chart(summary_stats, config)
        elif chart_type == "pie":
            spec = _generate_pie_chart(summary_stats, config)
        elif chart_type == "gauge":
            spec = _generate_gauge_chart(summary_stats, config)
        elif chart_type == "line":
            spec = _generate_line_chart(summary_stats, config)
        else:
            continue
            
        if spec:
            specs.append(spec)
    
    return specs


def _generate_bar_chart(summary_stats: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un graphique en barres."""
    keys = config.get("keys", [])
    title = config.get("title", "Statistiques")
    colors = config.get("colors", None)
    orientation = config.get("orientation", "vertical")  # vertical ou horizontal
    
    # Préparer les données
    data_values = []
    for key in keys:
        value = summary_stats.get(key)
        if value is not None:
            # Nettoyer la valeur (retirer % si présent)
            if isinstance(value, str) and '%' in value:
                value = float(value.replace('%', ''))
            data_values.append({"category": key, "value": value})
    
    if not data_values:
        return None
    
    # Configuration de base Vega-Lite
    if orientation == "horizontal":
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": title,
            "data": {"values": data_values},
            "mark": {"type": "bar"},
            "encoding": {
                "y": {"field": "category", "type": "nominal", "axis": {"title": None}, "sort": None},
                "x": {"field": "value", "type": "quantitative", "axis": {"title": "Valeur"}},
                "color": {
                    "field": "category",
                    "type": "nominal",
                    "legend": None,
                    "scale": {"range": colors} if colors else {}
                },
                "tooltip": [
                    {"field": "category", "type": "nominal", "title": "Catégorie"},
                    {"field": "value", "type": "quantitative", "title": "Valeur"}
                ]
            },
            "width": 500,
            "height": 300
        }
    else:
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": title,
            "data": {"values": data_values},
            "mark": {"type": "bar"},
            "encoding": {
                "x": {"field": "category", "type": "nominal", "axis": {"title": None, "labelAngle": -45}, "sort": None},
                "y": {"field": "value", "type": "quantitative", "axis": {"title": "Valeur"}},
                "color": {
                    "field": "category",
                    "type": "nominal",
                    "legend": None,
                    "scale": {"range": colors} if colors else {}
                },
                "tooltip": [
                    {"field": "category", "type": "nominal", "title": "Catégorie"},
                    {"field": "value", "type": "quantitative", "title": "Valeur"}
                ]
            },
            "width": 500,
            "height": 300
        }
    
    return spec


def _generate_pie_chart(summary_stats: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un graphique en camembert."""
    keys = config.get("keys", [])
    title = config.get("title", "Répartition")
    colors = config.get("colors", None)
    
    # Préparer les données
    data_values = []
    for key in keys:
        value = summary_stats.get(key)
        if value is not None:
            # Nettoyer la valeur (retirer % si présent)
            if isinstance(value, str) and '%' in value:
                value = float(value.replace('%', ''))
            data_values.append({"category": key, "value": value})
    
    if not data_values:
        return None
    
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title,
        "data": {"values": data_values},
        "mark": {"type": "arc", "innerRadius": 50},
        "encoding": {
            "theta": {"field": "value", "type": "quantitative"},
            "color": {
                "field": "category",
                "type": "nominal",
                "legend": {"title": None},
                "scale": {"range": colors} if colors else {}
            },
            "tooltip": [
                {"field": "category", "type": "nominal", "title": "Catégorie"},
                {"field": "value", "type": "quantitative", "title": "Valeur"}
            ]
        },
        "view": {"stroke": None},
        "width": 400,
        "height": 400
    }
    
    return spec


def _generate_gauge_chart(summary_stats: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un graphique de type jauge/indicateur pour afficher un taux.
    Utilise un arc chart pour simuler une jauge.
    """
    key = config.get("key")
    title = config.get("title", "Taux")
    max_value = config.get("max_value", 100)
    colors = config.get("colors", ["#F44336", "#FF9800", "#4CAF50"])  # Rouge, Orange, Vert
    thresholds = config.get("thresholds", [50, 80])  # Seuils pour les couleurs
    
    value = summary_stats.get(key)
    if value is None:
        return None
    
    # Nettoyer la valeur (retirer % si présent)
    if isinstance(value, str) and '%' in value:
        value = float(value.replace('%', ''))
    
    # Déterminer la couleur selon les seuils
    if value < thresholds[0]:
        color = colors[0]
    elif value < thresholds[1]:
        color = colors[1]
    else:
        color = colors[2]
    
    # Créer les données pour la jauge (valeur actuelle + reste)
    data_values = [
        {"category": "Valeur", "value": value, "order": 1},
        {"category": "Reste", "value": max_value - value, "order": 2}
    ]
    
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title,
        "data": {"values": data_values},
        "layer": [
            {
                "mark": {"type": "arc", "innerRadius": 80, "outerRadius": 120, "cornerRadius": 10},
                "encoding": {
                    "theta": {"field": "value", "type": "quantitative", "stack": True},
                    "color": {
                        "field": "category",
                        "type": "nominal",
                        "scale": {"domain": ["Valeur", "Reste"], "range": [color, "#E0E0E0"]},
                        "legend": None
                    },
                    "order": {"field": "order", "type": "ordinal"}
                }
            },
            {
                "mark": {
                    "type": "text",
                    "align": "center",
                    "baseline": "middle",
                    "fontSize": 32,
                    "fontWeight": "bold"
                },
                "encoding": {
                    "text": {"value": f"{value:.1f}%"}
                }
            }
        ],
        "view": {"stroke": None},
        "width": 300,
        "height": 300
    }
    
    return spec


def _generate_line_chart(summary_stats: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un graphique en lignes (pour évolutions temporelles si besoin futur)."""
    keys = config.get("keys", [])
    title = config.get("title", "Évolution")
    colors = config.get("colors", None)
    
    # Préparer les données
    data_values = []
    for key in keys:
        value = summary_stats.get(key)
        if value is not None:
            if isinstance(value, str) and '%' in value:
                value = float(value.replace('%', ''))
            data_values.append({"category": key, "value": value})
    
    if not data_values:
        return None
    
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title,
        "data": {"values": data_values},
        "mark": {"type": "line", "point": True},
        "encoding": {
            "x": {"field": "category", "type": "nominal", "axis": {"title": None, "labelAngle": -45}},
            "y": {"field": "value", "type": "quantitative", "axis": {"title": "Valeur"}},
            "color": {"value": colors[0] if colors else "#2196F3"},
            "tooltip": [
                {"field": "category", "type": "nominal", "title": "Catégorie"},
                {"field": "value", "type": "quantitative", "title": "Valeur"}
            ]
        },
        "width": 500,
        "height": 300
    }
    
    return spec


def create_html_with_vega(chart_specs: List[Dict[str, Any]]) -> str:
    """
    Crée un document HTML contenant tous les graphiques Vega-Lite.
    
    Args:
        chart_specs: Liste de spécifications Vega-Lite
        
    Returns:
        Chaîne HTML complète avec les graphiques embarqués
    """
    if not chart_specs:
        return "<html><body><p>Aucun graphique à afficher</p></body></html>"
    
    # Template HTML avec Vega-Embed
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .chart-container {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        #vis {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
    </style>
</head>
<body>
    <div id="vis"></div>
    <script type="text/javascript">
        const specs = {chart_specs_json};
        const container = document.getElementById('vis');
        
        specs.forEach((spec, index) => {{
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chart-container';
            chartDiv.id = 'chart-' + index;
            container.appendChild(chartDiv);
            
            vegaEmbed('#chart-' + index, spec, {{
                actions: {{
                    export: true,
                    source: false,
                    compiled: false,
                    editor: false
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    chart_specs_json = json.dumps(chart_specs, indent=2)
    html_content = html_template.format(chart_specs_json=chart_specs_json)
    
    return html_content
