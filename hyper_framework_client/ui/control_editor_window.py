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
__hyper_inputs__ = [
    {"key": "input_file", "label": "Fichier d'entrée (.csv)", "format": "csv"}
]

# === 2. Définition de la périodicité ===
# Valeurs possibles : 'WEEK', 'MONTH', 'QUARTER', 'SEMESTER'
__hyper_periodicity__ = 'WEEK'

# === Définitions des différentes importations ===
import pandas as pd
import os

# =============================================================================
# FONCTIONS DE TRAITEMENT
# =============================================================================

def charger_fichier(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Erreur lors du chargement du fichier : {e}")
        return pd.DataFrame({'Message': ['Hello World']})

def traiter_donnees(df):
    resultat_df = pd.DataFrame({
        'Colonne 1': ['Hello World'],
        'Colonne 2': ['Bienvenue dans Hyper-Framework'],
        'Statut': ['OK']
    })
    return resultat_df

def calculer_statistiques(df):
    stats = {
        'Nombre de lignes': len(df),
        'Nombre de colonnes': len(df.columns),
        'Message': 'Hello World'
    }
    return stats

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def run(input_file_paths, output_dir_path):
   

    Args:
        input_file_paths (dict): Dictionnaire contenant les chemins des fichiers d'entrée
        output_dir_path (str): Chemin du répertoire de sortie
    
    Returns:
        list: Liste de dictionnaires contenant les résultats à afficher
  
    results = []
    
    try:
        # --- Étape 1 : Chargement des fichiers ---
        input_df = charger_fichier(input_file_paths.get('input_file'))
        
        # --- Étape 2 : Traitement des données ---
        resultat_df = traiter_donnees(input_df)
        
        # --- Étape 3 : Calcul des statistiques ---
        stats = calculer_statistiques(resultat_df)
        
        # --- Étape 4 : Sauvegarde optionnelle (Excel) ---
        output_file = os.path.join(output_dir_path, "rapport_hello_world.xlsx")
        resultat_df.to_excel(output_file, index=False)
        print(f"Rapport sauvegardé : {output_file}")
        
        # --- Étape 5 : Structuration du résultat pour l'affichage ---
        results.append({
            'title': "Hello World - Exemple de Template",
            'dataframe': resultat_df,
            'display_columns': [
                {'key': 'Colonne 1', 'label': 'Message Principal'},
                {'key': 'Colonne 2', 'label': 'Description'},
                {'key': 'Statut', 'label': 'État'}
            ],
            'summary_stats': stats
        })
        
    except Exception as e:
        print(f"Une erreur est survenue durant l'exécution : {e}")
        import traceback
        traceback.print_exc()
        raise e
    
    return results
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