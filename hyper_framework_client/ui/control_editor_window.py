import customtkinter as ctk
from tkinter import messagebox
import re
from ..api.api_client import api_client

class ControlEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, user_data, control_id=None, read_only=False):
        super().__init__(parent)
        self.user_data = user_data
        self.control_id = control_id
        self.is_edit_mode = control_id is not None
        self.read_only = read_only
        
        title = "Visualisation" if self.read_only else ("Éditer" if self.is_edit_mode else "Créer")
        self.title(f"{title} du Contrôle")
        self.geometry("1000x800")
        
        self.grab_set()

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        # --- MODIFICATION --- La ligne qui s'étend est maintenant la 4ème (index 3)
        main_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(main_frame, text="Nom du Contrôle:").grid(row=0, column=0, sticky='w', pady=5, padx=10)
        self.name_entry = ctk.CTkEntry(main_frame)
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=10)
        
        ctk.CTkLabel(main_frame, text="Description:").grid(row=1, column=0, sticky='w', pady=5, padx=10)
        self.desc_entry = ctk.CTkEntry(main_frame)
        self.desc_entry.grid(row=1, column=1, sticky='ew', padx=10, pady=(0, 10))
        
        # --- NOUVEL EMPLACEMENT POUR LE BOUTON ---
        # Un conteneur pour aligner le bouton à droite
        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.grid(row=2, column=1, sticky='e', padx=10, pady=(5, 0))

        self.save_btn = ctk.CTkButton(button_container, text="Sauvegarder", command=self.save_control)
        self.save_btn.pack() # On le place simplement dans son conteneur

        # --- MODIFICATION --- Le cadre du script est déplacé à la ligne 3
        script_frame = ctk.CTkFrame(main_frame)
        script_frame.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=10, padx=10)
        self.script_text = ctk.CTkTextbox(script_frame, wrap='word', font=("Courier New", 12))
        self.script_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- L'ancien bouton a été retiré d'ici ---

        self._setup_syntax_highlighting()
        
        if self.is_edit_mode:
            self.load_control_data()
        else:
            self.insert_script_template()
        
        if self.read_only:
            self.apply_read_only_state()

        self.script_text.bind("<KeyRelease>", self._on_key_release)

    def _setup_syntax_highlighting(self):
        self.python_keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
        ]
        keyword_pattern = r'\b(' + '|'.join(self.python_keywords) + r')\b'
        self.highlight_patterns = {
            'comment': (r'#.*', '#999999', '#AAAAAA'),
            'string': (r'(\".*?\")|(\'.*?\')', '#CE9178', '#D69D85'),
            'keyword': (keyword_pattern, '#569CD6', '#C586C0'),
            'function_def': (r'\b(def|class)\b', '#4EC9B0', '#4EC9B0'),
            'numbers': (r'\b[0-9]+\b', '#B5CEA8', '#B5CEA8')
        }
        theme = ctk.get_appearance_mode()
        for tag_name, (pattern, light_color, dark_color) in self.highlight_patterns.items():
            color = light_color if theme == "Light" else dark_color
            self.script_text.tag_config(tag_name, foreground=color)

    def _on_key_release(self, event=None):
        self.after(50, self.highlight_syntax)

    def highlight_syntax(self):
        content = self.script_text.get("1.0", "end-1c")
        for tag in self.highlight_patterns.keys():
            self.script_text.tag_remove(tag, "1.0", "end")
        for tag, (pattern, _, _) in self.highlight_patterns.items():
            for match in re.finditer(pattern, content):
                start, end = match.span()
                self.script_text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

    def insert_script_template(self):
        template = """# Script d'analyse pour Hyper-Framework
#
# === 1. Définition des entrées ===
# Définissez ici les fichiers requis pour votre analyse
__hyper_inputs__ = [
    {"key": "fichier_principal", "label": "Fichier principal (.csv)", "format": "csv"},
    {"key": "fichier_secondaire", "label": "Fichier secondaire (.csv)", "format": "csv"}
]

# === 2. Définition de la périodicité ===
# Valeurs possibles : 'WEEK', 'MONTH', 'QUARTER', 'SEMESTER'
__hyper_periodicity__ = 'WEEK'

# === 3. Métadonnées du contrôle (RECOMMANDÉ) ===
# Ces métadonnées personnalisent l'en-tête du rapport PDF généré
# Le code de contrôle inclura automatiquement la date d'exécution
__hyper_control_metadata__ = {
    "application": "Application(s) concernée(s)",  # Ex: "CrowdStrike, Tanium, AD, GLPI, Intune"
    "layer": "Physique",  # "Physique", "Données", "Application", etc.
    "risk_reference": "R24",  # Référence du risque (ex: R24, R182, R211)
    "risk_name": "Nom du risque associé",  # Description courte du risque
    "control_name": "Nom du contrôle",  # Titre du contrôle
    "ref_description": "CTL_SSI_XXX_XXX_X",  # Référence description (ex: CTL_SSI_PHY_TMO_1)
    "description": "Description détaillée du contrôle et de ses objectifs.",
    "analyse": \"\"\"Points d'analyse réalisés :
• Premier point d'analyse
• Deuxième point d'analyse
• Troisième point d'analyse\"\"\"
}

# === 4. Définition des graphiques (OPTIONNEL) ===
# Si vous souhaitez afficher des graphiques interactifs, configurez cette section.
# Les graphiques sont générés automatiquement à partir des 'summary_stats' de vos résultats.
#
# Types de graphiques disponibles :
# - "bar"   : Graphique en barres (comparaisons)
# - "pie"   : Graphique circulaire (proportions)
# - "gauge" : Jauge/Indicateur (taux avec seuils)
# - "line"  : Graphique en lignes (évolutions)
#
# IMPORTANT : Les clés dans "keys" doivent EXACTEMENT correspondre aux clés 
#             de votre dictionnaire 'summary_stats' dans la fonction run()
#
__hyper_charts__ = [
    # Exemple 1 : Graphique en barres
    {
        "type": "bar",
        "title": "Statistiques générales",
        "keys": ["Nombre de lignes", "Nombre de colonnes"],  #  Doit correspondre à summary_stats
        "colors": ["#4CAF50", "#2196F3"],  # Optionnel : couleurs personnalisées
        "orientation": "vertical"  # "vertical" ou "horizontal"
    },
    
    # Exemple 2 : Graphique circulaire (décommentez pour l'utiliser)
    # {
    #     "type": "pie",
    #     "title": "Répartition des données",
    #     "keys": ["Catégorie A", "Catégorie B"],
    #     "colors": ["#4CAF50", "#F44336"]  # Vert et Rouge
    # },
    
    # Exemple 3 : Jauge pour un taux (décommentez pour l'utiliser)
    # {
    #     "type": "gauge",
    #     "title": "Taux de conformité",
    #     "key": "Taux",  #  Notez : "key" au singulier pour la jauge
    #     "max_value": 100,
    #     "colors": ["#F44336", "#FF9800", "#4CAF50"],  # Rouge, Orange, Vert
    #     "thresholds": [70, 90]  # <70% rouge, 70-90% orange, >90% vert
    # }
]

# === 4. Importations ===
import pandas as pd
import os

# =============================================================================
# FONCTIONS DE TRAITEMENT
# =============================================================================

def charger_fichier(file_path):
    \"\"\"Charge un fichier CSV et le convertit en DataFrame.\"\"\"
    try:
        df = pd.read_csv(file_path)
        print(f" Fichier chargé avec succès : {len(df)} lignes")
        return df
    except Exception as e:
        print(f" Erreur lors du chargement du fichier : {e}")
        # Retourne un DataFrame par défaut en cas d'erreur
        return pd.DataFrame({'Message': ['Hello World']})

def traiter_donnees(df):
    \"\"\"Traite les données et retourne un DataFrame avec les résultats.\"\"\"
    # --- VOTRE LOGIQUE DE TRAITEMENT ICI ---
    # Exemple simple : création d'un DataFrame de résultats
    resultat_df = pd.DataFrame({
        'Colonne 1': ['Hello World'],
        'Colonne 2': ['Bienvenue dans Hyper-Framework'],
        'Statut': ['OK']
    })
    return resultat_df

def calculer_statistiques(df):
    \"\"\"Calcule les statistiques à afficher dans l'interface.\"\"\"
    # --- STATISTIQUES PERSONNALISÉES ---
    # Ces statistiques seront affichées en haut des résultats
    # ET utilisées pour générer les graphiques si __hyper_charts__ est défini
    stats = {
        'Nombre de lignes': len(df),
        'Nombre de colonnes': len(df.columns),
        'Message': 'Hello World'
        # Ajoutez d'autres statistiques selon vos besoins :
        # 'Total éléments': total,
        # 'Conformes': conformes,
        # 'Non conformes': non_conformes,
        # 'Taux': f"{taux:.2f}%"
    }
    return stats

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def run(input_file_paths, output_dir_path):
    \"\"\"
    Fonction principale appelée par Hyper-Framework.
    
    Args:
        input_file_paths (dict): Dictionnaire contenant les chemins des fichiers d'entrée
                                 Format : {"key_du_fichier": "/chemin/complet/fichier.ext"}
        output_dir_path (str): Chemin du répertoire de sortie pour sauvegarder les fichiers Excel
    
    Returns:
        list: Liste de dictionnaires contenant les résultats à afficher.
              Chaque dictionnaire représente une section de résultats.
              
              Structure d'un résultat :
              {
                  'title': str,              # Titre de la section
                  'dataframe': DataFrame,    # Données à afficher (sera converti en 'items')
                  'display_columns': list,   # Colonnes à afficher avec leurs labels
                  'summary_stats': dict,     # Statistiques de résumé (pour graphiques)
                  'excel_output': str        # (Optionnel) Chemin du fichier Excel généré
              }
    \"\"\"
    results = []
    
    try:
        print("=" * 70)
        print("DÉBUT DE L'ANALYSE")
        print("=" * 70)
        
        # --- Étape 1 : Chargement des fichiers ---
        print("\\n[1/5] Chargement des fichiers...")
        input_df = charger_fichier(input_file_paths.get('input_file'))
        
        # --- Étape 2 : Traitement des données ---
        print("\\n[2/5] Traitement des données...")
        resultat_df = traiter_donnees(input_df)
        print(f" {len(resultat_df)} résultats générés")
        
        # --- Étape 3 : Calcul des statistiques ---
        print("\\n[3/5] Calcul des statistiques...")
        stats = calculer_statistiques(resultat_df)
        print(f" Statistiques calculées : {list(stats.keys())}")
        
        # --- Étape 4 : Sauvegarde optionnelle (Excel) ---
        print("\\n[4/5] Sauvegarde du rapport Excel...")
        output_file = os.path.join(output_dir_path, "rapport_hello_world.xlsx")
        resultat_df.to_excel(output_file, index=False, engine='openpyxl')
        print(f" Rapport sauvegardé : {output_file}")
        
        # --- Étape 5 : Filtrage et structuration pour l'affichage ---
        print("\\n[5/5] Préparation des résultats pour l'interface...")
        
        # IMPORTANT : Filtrer uniquement les résultats NOK pour l'affichage
        # L'interface affichera seulement les éléments non conformes
        resultat_nok = resultat_df[resultat_df['Statut'] == 'NOK'].copy()
        print(f" Résultats NOK à afficher : {len(resultat_nok)} sur {len(resultat_df)}")
        
        # Structuration du résultat
        results.append({
            'title': "Hello World - Exemple de Template",
            'dataframe': resultat_nok,  # Afficher uniquement les NOK
            'display_columns': [
                {'key': 'Colonne 1', 'label': 'Message Principal'},
                {'key': 'Colonne 2', 'label': 'Description'},
                {'key': 'Statut', 'label': 'État'}
            ],
            'summary_stats': stats,  # Important pour les graphiques !
            'excel_output': output_file  # (Optionnel)
        })
        
        print("\\n" + "=" * 70)
        print(" ANALYSE TERMINÉE AVEC SUCCÈS")
        print("=" * 70)
        
        # Si __hyper_charts__ est défini, les graphiques seront générés automatiquement
        # L'utilisateur verra un bouton " Voir les Graphiques" dans l'interface
        
    except Exception as e:
        print("\\n" + "=" * 70)
        print(" ERREUR DURANT L'EXÉCUTION")
        print("=" * 70)
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()
        raise e
    
    return results


# =============================================================================
# NOTES IMPORTANTES POUR LES DÉVELOPPEURS
# =============================================================================
#
# 1. MÉTADONNÉES DE CONTRÔLE (__hyper_control_metadata__) :
#    - Personnalise l'en-tête du rapport Word généré
#    - Un hexagone coloré affiche la conclusion (vert/jaune/rouge selon le taux)
#    - Voir GUIDE_METADONNEES_CONTROLE.md pour plus de détails
#
# 2. FILTRAGE DES RÉSULTATS AFFICHÉS :
#    - IMPORTANT : L'interface doit afficher UNIQUEMENT les éléments NOK
#    - Filtrez votre DataFrame avant de l'ajouter aux results
#    - Exemple : df_nok = df[df['Résultat'] == 'NOK'].copy()
#    - Les statistiques (summary_stats) doivent porter sur tous les résultats

# 3. GRAPHIQUES (__hyper_charts__) :
#    - Définissez cette section pour activer les graphiques interactifs
#    - Les clés dans "keys" doivent correspondre EXACTEMENT à celles de summary_stats
#    - Les graphiques s'affichent automatiquement si summary_stats est présent
#    - Voir GUIDE_GRAPHIQUES_VEGALITE.md pour la documentation complète
#
# 4. SUMMARY_STATS :
#    - Utilisé pour afficher les statistiques ET générer les graphiques
#    - Les valeurs peuvent être des nombres ou des strings avec "%"
#    - Doit calculer sur TOUTES les données (pas uniquement les NOK)
#    - Exemple : "Taux de conformité": "99.5%" ou "Taux de conformité": 99.5
#
# 5. DISPLAY_COLUMNS :
#    - Définit quelles colonnes du DataFrame afficher et leurs labels
#    - L'ordre des colonnes dans cette liste détermine l'ordre d'affichage
#    - Utilisez des labels clairs et descriptifs pour l'utilisateur final
#
# 6. EXCEL_OUTPUT :
#    - Optionnel, mais recommandé pour permettre le téléchargement
#    - Peut contenir plusieurs feuilles si besoin (analyse complète)
#    - Le fichier Excel peut inclure TOUTES les données (OK + NOK)
#
# =============================================================================
"""
        self.script_text.insert("1.0", template)
        self.highlight_syntax()

    def apply_read_only_state(self):
        self.name_entry.configure(state='disabled')
        self.desc_entry.configure(state='disabled')
        self.script_text.configure(state='disabled')
        # --- MODIFICATION --- On utilise pack_forget() au lieu de grid_remove()
        self.save_btn.pack_forget()

    def save_control(self):
        name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        script_code = self.script_text.get("1.0", "end-1c").strip()
        username = self.user_data['username']
        
        if not all([name, script_code]):
            messagebox.showerror("Erreur", "Le nom et le code du script sont obligatoires.", parent=self)
            return

        try:
            if self.is_edit_mode:
                api_client.update_control(self.control_id, name, description, script_code, username)
                messagebox.showinfo("Succès", f"Contrôle '{name}' mis à jour.", parent=self)
            else:
                api_client.create_control(name, description, script_code, username)
                messagebox.showinfo("Succès", f"Contrôle '{name}' créé.", parent=self)
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", str(e), parent=self)

    def load_control_data(self):
        try:
            username = self.user_data['username']
            data = api_client.get_control_details(self.control_id, username)
            self.name_entry.insert(0, data.get('name', ''))
            self.desc_entry.insert(0, data.get('description', ''))
            self.script_text.insert("1.0", data.get('script_code', ''))
            self.highlight_syntax()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le contrôle : {e}", parent=self)
            self.destroy()