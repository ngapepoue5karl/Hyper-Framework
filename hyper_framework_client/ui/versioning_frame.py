import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from ..api.api_client import api_client
from .themed_treeview import style_treeview
import datetime
import re


class VersioningFrame(ctk.CTkFrame):
    """
    Frame pour afficher l'historique des analyses exécutées.
    Permet de consulter les résultats d'analyses précédentes.
    """
    def __init__(self, master, app_parent, control_id=None, control_name=None):
        super().__init__(master)
        self.app_parent = app_parent
        self.runs_data = []
        self.current_run_details = None
        self.filter_control_id = control_id
        self.filter_control_name = control_name

        # Configuration de la grille
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # En-tête
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        # Titre dynamique selon le filtrage
        title_text = "Versioning - Historique des Analyses"
        if control_name:
            title_text = f"Versioning - Historique : {control_name}"
        
        ctk.CTkLabel(
            header_frame, 
            text=title_text, 
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Zone de recherche
        self.search_entry = ctk.CTkEntry(
            header_frame, 
            placeholder_text="Rechercher par nom de contrôle, semaine ou utilisateur..."
        )
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_runs)

        # Frame principal avec split gauche/droite
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)

        # Partie gauche : Liste des analyses
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame, 
            text="Analyses Exécutées", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

        # TreeView pour la liste des analyses
        tree_container = ctk.CTkFrame(left_frame)
        tree_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        cols = ('control_name', 'week_label', 'username', 'executed_at')
        self.tree = ttk.Treeview(tree_container, columns=cols, show='headings')
        
        self.tree.heading('control_name', text='Contrôle')
        self.tree.column('control_name', width=200)
        
        self.tree.heading('week_label', text='Semaine')
        self.tree.column('week_label', width=80, anchor='center')
        
        self.tree.heading('username', text='Utilisateur')
        self.tree.column('username', width=120)
        
        self.tree.heading('executed_at', text='Date d\'exécution')
        self.tree.column('executed_at', width=150, anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        style_treeview(self.tree)
        
        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)

        # Boutons d'actions
        action_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.view_btn = ctk.CTkButton(
            action_frame, 
            text="Voir les Résultats", 
            command=self.view_results,
            state='disabled'
        )
        self.view_btn.pack(side='left', padx=5, pady=5, expand=True, fill='x')

        self.export_btn = ctk.CTkButton(
            action_frame, 
            text="Exporter (Excel)", 
            command=self.export_results,
            state='disabled'
        )
        self.export_btn.pack(side='left', padx=5, pady=5, expand=True, fill='x')

        # Partie droite : Détails de l'analyse sélectionnée
        self.right_frame = ctk.CTkScrollableFrame(
            main_frame, 
            label_text="Détails de l'Analyse"
        )
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Message initial
        self.placeholder_label = ctk.CTkLabel(
            self.right_frame,
            text="Sélectionnez une analyse pour voir les détails",
            font=ctk.CTkFont(size=14, slant='italic'),
            text_color="gray"
        )
        self.placeholder_label.pack(pady=50)

        # Charger la liste des analyses
        self.load_and_display_runs()

    def load_and_display_runs(self):
        """Charge la liste des analyses depuis le serveur"""
        try:
            username = self.app_parent.user_data['username']
            self.runs_data = api_client.get_analysis_runs(username)
            self.filter_runs()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'historique: {e}", parent=self)

    def filter_runs(self, event=None):
        """Filtre la liste des analyses selon le texte de recherche et le control_id"""
        search_term = self.search_entry.get().lower()
        
        # Vider le TreeView
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Remplir avec les données filtrées
        for run in self.runs_data:
            # Si un filtre par control_id est actif, n'afficher que les runs de ce contrôle
            if self.filter_control_id is not None and str(run.get('control_id')) != str(self.filter_control_id):
                continue
            
            control_name = run.get('control_name', '').lower()
            week_label = run.get('week_label', '').lower()
            username = run.get('username', '').lower()
            executed_at = run.get('executed_at', '')
            
            if (search_term in control_name or 
                search_term in week_label or 
                search_term in username):
                
                # Formater la date pour l'affichage
                display_date = self._format_datetime(executed_at)
                
                self.tree.insert('', 'end', iid=run['id'], values=(
                    run.get('control_name', ''),
                    run.get('week_label', ''),
                    run.get('username', ''),
                    display_date
                ))
        
        self.on_selection_change()

    def _format_datetime(self, datetime_str):
        """Formate une date ISO en format lisible"""
        try:
            dt = datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return datetime_str

    def on_selection_change(self, event=None):
        """Active/désactive les boutons selon la sélection"""
        if self.tree.selection():
            self.view_btn.configure(state='normal')
            self.export_btn.configure(state='normal')
        else:
            self.view_btn.configure(state='disabled')
            self.export_btn.configure(state='disabled')
            self.current_run_details = None

    def view_results(self):
        """Affiche les résultats de l'analyse sélectionnée"""
        if not self.tree.selection():
            return
        
        run_id = self.tree.selection()[0]
        
        try:
            username = self.app_parent.user_data['username']
            self.current_run_details = api_client.get_analysis_run_details(run_id, username)
            
            # Vider le frame de droite
            for widget in self.right_frame.winfo_children():
                widget.destroy()
            
            # Afficher les informations générales
            info_frame = ctk.CTkFrame(self.right_frame)
            info_frame.pack(fill='x', pady=10, padx=5)
            
            ctk.CTkLabel(
                info_frame,
                text=f" {self.current_run_details['control_name']}",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor='w', padx=10, pady=5)
            
            details_text = (
                f" Semaine : {self.current_run_details['week_label']}\n"
                f" Utilisateur : {self.current_run_details['username']}\n"
                f" Exécuté le : {self._format_datetime(self.current_run_details['executed_at'])}"
            )
            
            ctk.CTkLabel(
                info_frame,
                text=details_text,
                font=ctk.CTkFont(size=12),
                justify='left'
            ).pack(anchor='w', padx=10, pady=5)
            
            # Afficher les fichiers utilisés
            if self.current_run_details.get('files_info'):
                files_frame = ctk.CTkFrame(self.right_frame)
                files_frame.pack(fill='x', pady=10, padx=5)
                
                ctk.CTkLabel(
                    files_frame,
                    text=" Fichiers utilisés :",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).pack(anchor='w', padx=10, pady=5)
                
                for file_info in self.current_run_details['files_info']:
                    file_text = f"  • {file_info.get('key', '')} : {file_info.get('original_name', '')}"
                    ctk.CTkLabel(
                        files_frame,
                        text=file_text,
                        font=ctk.CTkFont(size=11)
                    ).pack(anchor='w', padx=20, pady=2)
            
            # Afficher les résultats
            results_data = self.current_run_details.get('results_json', [])
            if results_data:
                for section in results_data:
                    self.create_result_section(self.right_frame, section)
            else:
                ctk.CTkLabel(
                    self.right_frame,
                    text="Aucun résultat disponible",
                    font=ctk.CTkFont(slant='italic'),
                    text_color="gray"
                ).pack(pady=20)
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les détails: {e}", parent=self)

    def create_result_section(self, parent, data):
        """Crée une section de résultats (identique à GenericAnalysisFrame)"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10, padx=5)
        
        ctk.CTkLabel(
            frame, 
            text=data.get('title', 'Section'), 
            font=ctk.CTkFont(weight='bold')
        ).pack(anchor='w', padx=10, pady=5)
        
        # Statistiques résumées
        stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        stats_frame.pack(fill='x', pady=(0, 10))
        summary_stats = data.get('summary_stats', {})
        
        if summary_stats:
            # Première ligne pour les statistiques principales
            first_row_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            first_row_frame.pack(fill='x', anchor='w')

            # Deuxième ligne pour le Taux
            second_row_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            second_row_frame.pack(fill='x', anchor='w', pady=(5, 0))

            for key, value in summary_stats.items():
                stat_text = f"{key}: {value}"
                if key == "Taux":
                    ctk.CTkLabel(
                        second_row_frame, 
                        text=stat_text, 
                        font=ctk.CTkFont(weight='bold')
                    ).pack(side='left', padx=15)
                else:
                    ctk.CTkLabel(
                        first_row_frame, 
                        text=stat_text, 
                        font=ctk.CTkFont(weight='bold')
                    ).pack(side='left', padx=15)

        # Tableau des données
        items = data.get('items', [])
        display_columns = data.get('display_columns', [])
        
        if items and display_columns:
            tree_frame = ctk.CTkFrame(frame)
            tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
            tree_frame.columnconfigure(0, weight=1)
            tree_frame.rowconfigure(0, weight=1)
            
            column_keys = [col_def['key'] for col_def in display_columns]
            tree = ttk.Treeview(tree_frame, columns=column_keys, show='headings', height=min(len(items), 15))
            
            for col_def in display_columns:
                tree.heading(col_def['key'], text=col_def['label'])
                tree.column(col_def['key'], width=200, minwidth=100)
            
            for item in items:
                tree.insert('', 'end', values=[item.get(key, '') for key in column_keys])
            
            tree.grid(row=0, column=0, sticky='nsew')
            style_treeview(tree)

            ysb = ctk.CTkScrollbar(tree_frame, command=tree.yview)
            ysb.grid(row=0, column=1, sticky='ns')
            xsb = ctk.CTkScrollbar(tree_frame, command=tree.xview, orientation="horizontal")
            xsb.grid(row=1, column=0, sticky='ew')
            tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        else:
            ctk.CTkLabel(
                frame, 
                text="Aucun élément à afficher.", 
                font=ctk.CTkFont(slant='italic')
            ).pack(padx=10, pady=10)

    def export_results(self):
        """Exporte les résultats de l'analyse sélectionnée en Excel"""
        if not self.current_run_details:
            messagebox.showwarning("Aucune sélection", "Veuillez d'abord voir les résultats.", parent=self)
            return
        
        results_data = self.current_run_details.get('results_json', [])
        if not results_data:
            messagebox.showwarning("Aucune donnée", "Cette analyse ne contient aucun résultat.", parent=self)
            return
        
        # Créer un nom de fichier par défaut
        safe_name = re.sub(r'[^\w\.-]', '_', self.current_run_details.get('control_name', 'analyse'))
        week = self.current_run_details.get('week_label', 'SXX')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        default_filename = f"Resultats_{safe_name}_{week}_{timestamp}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel", "*.xlsx")],
            parent=self
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for i, section in enumerate(results_data):
                    items = section.get('items', [])
                    display_columns = section.get('display_columns', [])
                    
                    if not items or not display_columns:
                        continue
                    
                    # Nom de la feuille (limité à 31 caractères)
                    title = re.sub(r'[\\/*?:\[\]]', '', section.get('title', f'Resultat_{i+1}'))[:31]
                    
                    column_keys = [col['key'] for col in display_columns]
                    column_labels = {col['key']: col['label'] for col in display_columns}

                    df = pd.DataFrame(items)[column_keys].rename(columns=column_labels)
                    df.to_excel(writer, sheet_name=title, index=False)
            
            messagebox.showinfo("Succès", f"Fichier Excel exporté:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Erreur d'exportation", f"Une erreur est survenue :\n{e}", parent=self)
