import customtkinter as ctk
from tkinter import ttk, messagebox
from ..api.api_client import api_client
from ..auth_roles import Role, Permission
from .themed_treeview import style_treeview

class UpdateUserDialog(ctk.CTkToplevel):
    def __init__(self, parent, user_data, current_user_role):
        super().__init__(parent)
        self.user_data = user_data
        self.current_user_role = current_user_role
        self.result = None

        self.title(f"Mise à jour de {self.user_data['username']}")
        self.geometry("400x250")
        self.grab_set()

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=20, pady=20, expand=True, fill="both")
        
        ctk.CTkLabel(main_frame, text="Nom d'utilisateur:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_var = ctk.StringVar(value=self.user_data['username'])
        self.username_entry = ctk.CTkEntry(main_frame, textvariable=self.username_var, width=250)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(main_frame, text="Rôle:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.role_var = ctk.StringVar(value=self.user_data['role'])
        
        if self.current_user_role == Role.SUPER_ADMIN:
            role_values = [r.value for r in Role if r != Role.SUPER_ADMIN]
        else:
            role_values = [r.value for r in Role if r in [Role.ANALYST, Role.AUDITOR]]
            
        self.role_combobox = ctk.CTkComboBox(main_frame, variable=self.role_var, values=role_values, state='readonly')
        self.role_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Valider", command=self.ok).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=self.cancel, fg_color="gray").pack(side="left", padx=10)

        self.username_entry.focus_set()

    def ok(self, event=None):
        self.result = {'username': self.username_var.get(), 'role': self.role_var.get()}
        self.destroy()

    def cancel(self, event=None):
        self.destroy()

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master)
        self.app_parent = app_parent
        self.current_user_data = app_parent.user_data
        self.current_user_role = Role(self.current_user_data['role'])
        self.users_data = [] # Pour stocker la liste complète des utilisateurs

        # Vérifier les permissions en amont pour adapter l'affichage
        self.can_manage = self.app_parent.has_permission(Permission.MANAGE_USERS)
        
        if self.can_manage:
            self.grid_columnconfigure(0, weight=3) # Liste des utilisateurs
            self.grid_columnconfigure(1, weight=1) # Panneau d'actions
        else:
            self.grid_columnconfigure(0, weight=1) # La liste prend toute la place
        self.grid_rowconfigure(0, weight=1)

        # Cadre pour la liste et la recherche (toujours visible)
        left_panel = ctk.CTkFrame(self)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_panel, text="Liste des Utilisateurs", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=(5,0))
        self.search_entry = ctk.CTkEntry(left_panel, placeholder_text="Rechercher par nom d'utilisateur...")
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(5,10), padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_users)

        list_frame = ctk.CTkFrame(left_panel)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        cols = ('username', 'role')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        self.tree.heading('username', text='Nom d\'utilisateur'); self.tree.column('username', width=200)
        self.tree.heading('role', text='Rôle'); self.tree.column('role', width=150)
        self.tree.grid(row=0, column=0, sticky='nsew')
        style_treeview(self.tree)
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Afficher le panneau d'actions et lier les événements uniquement si l'utilisateur a les droits
        if self.can_manage:
            self.tree.bind('<<TreeviewSelect>>', self.on_user_select)
            self.tree.bind('<Button-1>', self.on_tree_click)

            action_frame = ctk.CTkFrame(self)
            action_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            creation_frame = ctk.CTkFrame(action_frame)
            creation_frame.pack(fill='x', padx=10, pady=10)
            ctk.CTkLabel(creation_frame, text="Créer un Nouvel Utilisateur", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 10))
            ctk.CTkLabel(creation_frame, text="Nom d'utilisateur:").pack(anchor='w')
            self.create_username_entry = ctk.CTkEntry(creation_frame)
            self.create_username_entry.pack(pady=5, fill='x')
            ctk.CTkLabel(creation_frame, text="Rôle:").pack(anchor='w')
            self.create_role_var = ctk.StringVar()
            self.create_role_combobox = ctk.CTkComboBox(creation_frame, variable=self.create_role_var, state='readonly', values=[r.value for r in Role if r != Role.SUPER_ADMIN])
            self.create_role_combobox.pack(pady=5, fill='x')
            self.create_btn = ctk.CTkButton(creation_frame, text="Créer Utilisateur", command=self.create_user)
            self.create_btn.pack(pady=(10, 5), fill='x')
            
            selection_frame = ctk.CTkFrame(action_frame)
            selection_frame.pack(fill='x', padx=10, pady=20)
            ctk.CTkLabel(selection_frame, text="Actions sur la Sélection", font=ctk.CTkFont(weight="bold")).pack(anchor='w')
            self.update_btn = ctk.CTkButton(selection_frame, text="Mettre à jour...", command=self.open_update_dialog)
            self.update_btn.pack(pady=5, fill='x')
            self.delete_btn = ctk.CTkButton(selection_frame, text="Supprimer...", command=self.delete_user, fg_color="#D32F2F", hover_color="#B71C1C")
            self.delete_btn.pack(pady=5, fill='x')
        
        self.refresh_user_list()

    def set_creation_mode(self):
        if not self.can_manage: return
        if self.tree.selection(): self.tree.selection_remove(self.tree.selection()[0])
        self.update_btn.configure(state='disabled')
        self.delete_btn.configure(state='disabled')
        self.create_username_entry.configure(state='normal')
        self.create_username_entry.delete(0, ctk.END)
        self.create_role_combobox.configure(state='readonly')
        self.create_role_var.set('')
        self.create_btn.configure(state='normal')

    def set_selection_mode(self):
        if not self.can_manage: return
        if not self.tree.selection(): return
        item = self.tree.item(self.tree.selection()[0])
        selected_role = Role(item['values'][1])
        can_update, can_delete = False, False
        if self.current_user_role == Role.SUPER_ADMIN:
            if selected_role != Role.SUPER_ADMIN: can_update, can_delete = True, True
        elif self.current_user_role == Role.ADMIN:
            if selected_role in [Role.ANALYST, Role.AUDITOR]: can_update, can_delete = True, True
        self.update_btn.configure(state='normal' if can_update else 'disabled')
        self.delete_btn.configure(state='normal' if can_delete else 'disabled')
        self.create_username_entry.delete(0, ctk.END)
        self.create_username_entry.configure(state='disabled')
        self.create_role_combobox.set('')
        self.create_role_combobox.configure(state='disabled')
        self.create_btn.configure(state='disabled')

    def on_user_select(self, event):
        if self.tree.selection(): self.set_selection_mode()

    def on_tree_click(self, event):
        if self.tree.identify_region(event.x, event.y) == "nothing": self.set_creation_mode()
    
    def refresh_user_list(self):
        if self.can_manage:
            self.set_creation_mode()
        else:
            if self.tree.selection(): self.tree.selection_remove(self.tree.selection()[0])
            
        try:
            current_username = self.current_user_data['username']
            self.users_data = api_client.get_all_users(current_username)
            self.users_data.sort(key=lambda x: x['username'].lower())
            self.filter_users()
        except Exception as e: messagebox.showerror("Erreur", f"Impossible de charger les utilisateurs: {e}", parent=self)
    
    def filter_users(self, event=None):
        search_term = self.search_entry.get().lower()
        for i in self.tree.get_children(): self.tree.delete(i)
        
        for user in self.users_data:
            if search_term in user['username'].lower():
                self.tree.insert('', 'end', iid=user['id'], values=(user['username'], user['role']))
        
        # Désactiver les boutons de sélection si rien n'est sélectionné après le filtre
        if not self.tree.selection() and self.can_manage:
            self.update_btn.configure(state='disabled')
            self.delete_btn.configure(state='disabled')

    def create_user(self):
        username, role_str = self.create_username_entry.get(), self.create_role_var.get()
        if not username or not role_str: return messagebox.showerror("Erreur", "Le nom et le rôle sont requis.", parent=self)
        try:
            res = api_client.create_user(username, role_str)
            messagebox.showinfo("Succès", f"Utilisateur '{res['username']}' créé.\nMot de passe: {res['temporary_password']}", parent=self)
            self.refresh_user_list()
        except Exception as e: messagebox.showerror("Erreur", str(e), parent=self)

    def open_update_dialog(self):
        if not self.tree.selection(): return
        item = self.tree.item(self.tree.selection()[0])
        user_id = self.tree.selection()[0]
        user_data = {'id': user_id, 'username': item['values'][0], 'role': item['values'][1]}
        
        dialog = UpdateUserDialog(self, user_data, self.current_user_role)
        self.wait_window(dialog)
        
        if dialog.result:
            new_data = dialog.result
            if new_data['username'] == user_data['username'] and new_data['role'] == user_data['role']: return
            try:
                current_username = self.current_user_data['username']
                api_client.update_user(user_data['id'], current_username, new_data['username'], new_data['role'])
                messagebox.showinfo("Succès", "Utilisateur mis à jour.", parent=self)
                self.refresh_user_list()
            except Exception as e: messagebox.showerror("Erreur", str(e), parent=self)

    def delete_user(self):
        if not self.tree.selection(): return
        item = self.tree.item(self.tree.selection()[0])
        user_id = self.tree.selection()[0]
        username = item['values'][0]
        if messagebox.askyesno("Confirmer", f"Supprimer l'utilisateur '{username}' ?", parent=self, icon='warning'):
            try:
                api_client.delete_user(user_id)
                messagebox.showinfo("Succès", "Utilisateur supprimé.", parent=self)
                self.refresh_user_list()
            except Exception as e: messagebox.showerror("Erreur", str(e), parent=self)