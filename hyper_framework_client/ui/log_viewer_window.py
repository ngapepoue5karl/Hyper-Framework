#---> FICHIER MODIFIÉ : hyper_framework_client/ui/log_viewer_window.py

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from ..api.api_client import api_client
from .themed_treeview import style_treeview
import datetime
import json

class LogViewerFrame(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master)
        self.app_parent = app_parent
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(action_frame, text="Journal d'Activité", font=ctk.CTkFont(size=16, weight="bold")).pack(side='left', padx=10)
        
        right_button_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        right_button_frame.pack(side='right')

        self.export_btn = ctk.CTkButton(right_button_frame, text="Exporter les Logs", command=self.export_logs_to_file)
        self.export_btn.pack(side='left', padx=10, pady=10)

        ctk.CTkButton(right_button_frame, text="Rafraîchir", command=self.refresh_logs).pack(side='left', padx=10, pady=10)

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        cols = ('timestamp', 'username', 'role', 'action', 'status', 'ip_address', 'details')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        
        self.tree.heading('timestamp', text='Date et Heure'); self.tree.column('timestamp', width=160)
        self.tree.heading('username', text='Utilisateur'); self.tree.column('username', width=120)
        self.tree.heading('role', text='Rôle'); self.tree.column('role', width=100)
        self.tree.heading('action', text='Action'); self.tree.column('action', width=150)
        self.tree.heading('status', text='Statut'); self.tree.column('status', width=80, anchor='center')
        self.tree.heading('ip_address', text='Adresse IP'); self.tree.column('ip_address', width=120)
        self.tree.heading('details', text='Détails'); self.tree.column('details', width=400)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        style_treeview(self.tree)
        
        self.tree.tag_configure('failure', foreground='#E57373')
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.refresh_logs()

    def refresh_logs(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        try:
            current_username = self.app_parent.user_data['username']
            logs = api_client.get_logs(current_username)
            
            for log in logs:
                tags = ('failure',) if log.get('status') == 'FAILURE' else ()
                timestamp = log.get('timestamp', '').replace('T', ' ').split('.')[0]
                details = log.get('details', {})
                details_str = json.dumps(details) if isinstance(details, dict) else str(details)

                self.tree.insert('', 'end', values=(
                    timestamp,
                    log.get('username', ''),
                    log.get('user_role', ''),
                    log.get('action', ''),
                    log.get('status', ''),
                    log.get('ip_address', ''),
                    details_str
                ), tags=tags)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les logs: {e}", parent=self)

    def export_logs_to_file(self):
        try:
            default_filename = f"export_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            save_path = filedialog.asksaveasfilename(
                title="Enregistrer l'export des logs",
                initialfile=default_filename,
                defaultextension=".txt",
                filetypes=[("Fichiers Texte", "*.txt"), ("Tous les fichiers", "*.*")],
                parent=self
            )
            
            if not save_path:
                return

            username = self.app_parent.user_data['username']
            log_content = api_client.export_logs(username)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            messagebox.showinfo("Succès", f"Les logs ont été exportés avec succès vers :\n{save_path}", parent=self)

        except Exception as e:
            messagebox.showerror("Erreur d'exportation", f"Une erreur est survenue lors de l'exportation : {e}", parent=self)