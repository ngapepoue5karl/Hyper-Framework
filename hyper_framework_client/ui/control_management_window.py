# hyper_framework_client/ui/control_management_window.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from ..api.api_client import api_client
from ..auth_roles import Role, Permission, ROLE_PERMISSIONS
from .control_editor_window import ControlEditorWindow
from .themed_treeview import style_treeview

class ControlManagementFrame(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master)
        self.app_parent = app_parent
        self.user_data = app_parent.user_data
        self.user_role = Role(self.user_data['role'])

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Cadre des Actions ---
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        can_manage = self.has_permission(Permission.MANAGE_CONTROLS)
        can_edit = self.has_permission(Permission.EDIT_CONTROLS)
        can_delete = self.has_permission(Permission.DELETE_CONTROLS)

        self.create_btn = ctk.CTkButton(action_frame, text="Créer un Contrôle", command=self.create_new_control, state='normal' if can_manage else 'disabled')
        self.create_btn.pack(side='left', padx=10, pady=10)
        
        self.edit_btn = ctk.CTkButton(action_frame, text="Éditer", command=self.edit_selected_control, state='normal' if can_edit else 'disabled')
        self.edit_btn.pack(side='left', padx=10, pady=10)

        self.view_btn = ctk.CTkButton(action_frame, text="Voir", command=lambda: self.edit_selected_control(read_only=True))
        self.view_btn.pack(side='left', padx=10, pady=10)

        self.delete_btn = ctk.CTkButton(action_frame, text="Supprimer", command=self.delete_selected_control, state='normal' if can_delete else 'disabled', fg_color="#D32F2F", hover_color="#B71C1C")
        self.delete_btn.pack(side='right', padx=10, pady=10)
        
        ctk.CTkButton(action_frame, text="Rafraîchir", command=self.refresh_control_list).pack(side='right', padx=10, pady=10)

        # --- Liste des contrôles ---
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        cols = ('name', 'description', 'updated_at', 'last_updated_by')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        
        self.tree.heading('name', text='Nom'); self.tree.column('name', width=250)
        self.tree.heading('description', text='Description'); self.tree.column('description', width=350)
        self.tree.heading('updated_at', text='Dernière MàJ'); self.tree.column('updated_at', width=150)
        self.tree.heading('last_updated_by', text='Mis à jour par'); self.tree.column('last_updated_by', width=120)
        self.tree.grid(row=0, column=0, sticky='nsew')
        style_treeview(self.tree)
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.refresh_control_list()

    def has_permission(self, permission: Permission):
        return permission in ROLE_PERMISSIONS.get(self.user_role, set())

    def refresh_control_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            # --- CORRECTION DE L'ERREUR ICI ---
            # Ajout de l'argument 'username' manquant à l'appel de l'API
            username = self.user_data['username']
            controls = api_client.get_all_controls(username)
            # --- FIN DE LA CORRECTION ---

            controls.sort(key=lambda x: x['name'].lower())
            for ctrl in controls:
                self.tree.insert('', 'end', iid=ctrl['id'], values=(
                    ctrl['name'], ctrl.get('description', ''),
                    ctrl.get('updated_at', ''), ctrl.get('last_updated_by', '')
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les contrôles: {e}", parent=self)

    def create_new_control(self):
        editor = ControlEditorWindow(self, self.user_data, control_id=None)
        self.wait_window(editor)
        self.refresh_control_list()

    def edit_selected_control(self, read_only=False):
        if not self.tree.selection():
            return messagebox.showwarning("Sélection requise", "Veuillez sélectionner un contrôle.", parent=self)
        
        control_id = self.tree.selection()[0]
        
        editor = ControlEditorWindow(self, self.user_data, control_id=control_id, read_only=read_only)
        self.wait_window(editor)
        self.refresh_control_list()

    def delete_selected_control(self):
        if not self.tree.selection():
            return messagebox.showwarning("Sélection requise", "Veuillez sélectionner un contrôle.", parent=self)

        selection_id = self.tree.selection()[0]
        item = self.tree.item(selection_id)
        control_id = selection_id
        control_name = item['values'][0]
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer '{control_name}' ?", parent=self):
            try:
                username = self.user_data['username']
                api_client.delete_control(control_id, username)
                messagebox.showinfo("Succès", "Contrôle supprimé.", parent=self)
                self.refresh_control_list()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le contrôle: {e}", parent=self)