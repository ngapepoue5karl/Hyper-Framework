#---> CONTENU COMPLET pour hyper_framework_client/ui/analysis_selection_frame.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from ..api.api_client import api_client
from .themed_treeview import style_treeview
from ..auth_roles import Role

class AnalysisSelectionFrame(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master)
        self.app_parent = app_parent
        self.controls_data = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header_frame, text="Sélectionner une Analyse", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        
        self.search_entry = ctk.CTkEntry(header_frame, placeholder_text="Rechercher un contrôle par nom ou description...")
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_controls)

        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.run_btn = ctk.CTkButton(action_frame, text="Lancer l'Analyse Sélectionnée", height=40, command=self.launch_analysis, state='disabled')
        self.run_btn.pack(side='right', padx=10, pady=5)

        # Si l'utilisateur est un auditeur, on désactive le bouton de manière permanente
        # et on change son texte pour plus de clarté.
        if self.app_parent.user_role == Role.AUDITOR:
            self.run_btn.configure(state='disabled', text="Exécution non autorisée pour ce rôle")

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        cols = ('name', 'description', 'updated_at', 'last_updated_by')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        
        self.tree.heading('name', text='Nom'); self.tree.column('name', width=300)
        self.tree.heading('description', text='Description'); self.tree.column('description', width=450)
        self.tree.heading('updated_at', text='Dernière MàJ'); self.tree.column('updated_at', width=150, anchor='center')
        self.tree.heading('last_updated_by', text='Mis à jour par'); self.tree.column('last_updated_by', width=150)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        style_treeview(self.tree)
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)
        
        self.load_and_display_controls()

    def load_and_display_controls(self):
        try:
            username = self.app_parent.user_data['username']
            self.controls_data = api_client.get_all_controls(username)
            self.controls_data.sort(key=lambda x: x['name'].lower())
            self.filter_controls()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les contrôles: {e}", parent=self)

    def filter_controls(self, event=None):
        search_term = self.search_entry.get().lower()
        for i in self.tree.get_children(): self.tree.delete(i)
        for ctrl in self.controls_data:
            name = ctrl.get('name', '').lower()
            desc = ctrl.get('description', '').lower()
            if search_term in name or search_term in desc:
                self.tree.insert('', 'end', iid=ctrl['id'], values=(
                    ctrl['name'], 
                    ctrl.get('description', ''),
                    ctrl.get('updated_at', ''), 
                    ctrl.get('last_updated_by', '')
                ))
        self.on_selection_change()

    def on_selection_change(self, event=None):
        # On ajoute une garde pour s'assurer que le bouton ne s'active jamais pour un auditeur
        if self.app_parent.user_role == Role.AUDITOR:
            self.run_btn.configure(state='disabled')
            return
        
        if self.tree.selection():
            self.run_btn.configure(state='normal')
        else:
            self.run_btn.configure(state='disabled')

    def launch_analysis(self):
        # On peut aussi ajouter une sécurité ici, bien que le bouton soit désactivé
        if self.app_parent.user_role == Role.AUDITOR:
            return
            
        if not self.tree.selection():
            return
        control_id = self.tree.selection()[0]
        self.app_parent.open_selected_analysis(control_id)