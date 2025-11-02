#---> CONTENU COMPLET pour hyper_framework_client/ui/main_window.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from ..api.api_client import api_client
from ..auth_roles import Role, Permission, ROLE_PERMISSIONS

# Importation des vues (Frames)
from .user_management_window import UserManagementFrame
from .control_management_window import ControlManagementFrame
from .generic_analysis_window import GenericAnalysisFrame
from .log_viewer_window import LogViewerFrame
from .analysis_selection_frame import AnalysisSelectionFrame

# --- NOUVELLE FENÊTRE DE DIALOGUE ENTIÈREMENT EN CUSTOMTKINTER ---
class ChangePasswordDialog(ctk.CTkToplevel):
    """
    Une fenêtre de dialogue modale personnalisée pour le changement de mot de passe,
    entièrement construite avec CustomTkinter pour une intégration visuelle parfaite.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("Changer le mot de passe")
        self.geometry("400x200")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Rend la fenêtre modale
        self.grab_set()
        self.transient(parent)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Vous devez définir un nouveau mot de passe.").pack(pady=(0, 10))

        self.password_entry = ctk.CTkEntry(main_frame, show="*", width=300)
        self.password_entry.pack(pady=5)
        self.password_entry.focus()

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Valider", command=self._on_ok).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", fg_color="gray", command=self._on_cancel).pack(side="left", padx=10)

        # Lier la touche Entrée à la validation
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Mot de passe vide", "Le mot de passe ne peut pas être vide.", parent=self)
            return
        self.result = password
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

class MainWindow(ctk.CTkToplevel):
    def __init__(self, parent, user_data):
        super().__init__(parent)
        self.login_window = parent
        self.user_data = user_data
        self.user_role = Role(user_data['role'])

        self.title(f"Hyper-Framework - Bienvenue {self.user_data['username']}")
        self.geometry("1280x720")

        self.check_temporary_password()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.nav_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        self.nav_frame.grid_rowconfigure(5, weight=1) # Espace pour pousser les boutons du bas

        self.app_title = ctk.CTkLabel(self.nav_frame, text="Hyper-Framework", font=ctk.CTkFont(size=20, weight="bold"))
        self.app_title.grid(row=0, column=0, padx=20, pady=20)

        # Boutons de navigation
        self.home_button = ctk.CTkButton(self.nav_frame, text="Accueil", command=self.show_home_frame)
        self.home_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        if self.has_permission(Permission.VIEW_CONTROLS):
            self.control_mgmt_button = ctk.CTkButton(self.nav_frame, text="Gestion Contrôles", command=self.show_control_management_frame)
            self.control_mgmt_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        if self.has_permission(Permission.VIEW_USERS):
            self.user_mgmt_button = ctk.CTkButton(self.nav_frame, text="Gestion Utilisateurs", command=self.show_user_management_frame)
            self.user_mgmt_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Le bouton n'est affiché que si l'utilisateur a la permission VIEW_LOGS
        if self.has_permission(Permission.VIEW_LOGS):
            self.log_viewer_button = ctk.CTkButton(self.nav_frame, text="Journal d'Activité", command=self.show_log_viewer_frame)
            self.log_viewer_button.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Boutons du bas (remontés)
        self.logout_button = ctk.CTkButton(self.nav_frame, text="Déconnexion", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.logout)
        self.logout_button.grid(row=9, column=0, padx=20, pady=10, sticky="ew")
        self.exit_button = ctk.CTkButton(self.nav_frame, text="Quitter", fg_color="#D32F2F", hover_color="#B71C1C", command=self.exit_application)
        self.exit_button.grid(row=10, column=0, padx=20, pady=10, sticky="ew")
        
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.current_frame = None

        self.show_home_frame()

    def clear_main_content(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_home_frame(self):
        self.clear_main_content()
        self.current_frame = AnalysisSelectionFrame(self.main_content_frame, self)
        self.current_frame.pack(expand=True, fill="both")

    def show_user_management_frame(self):
        self.clear_main_content()
        self.current_frame = UserManagementFrame(self.main_content_frame, self)
        self.current_frame.pack(expand=True, fill="both")

    def show_control_management_frame(self):
        self.clear_main_content()
        self.current_frame = ControlManagementFrame(self.main_content_frame, self)
        self.current_frame.pack(expand=True, fill="both")

    def show_log_viewer_frame(self):
        self.clear_main_content()
        self.current_frame = LogViewerFrame(self.main_content_frame, self)
        self.current_frame.pack(expand=True, fill="both")

    def open_selected_analysis(self, control_id):
        if control_id:
            self.clear_main_content()
            self.current_frame = GenericAnalysisFrame(self.main_content_frame, self, control_id)
            self.current_frame.pack(expand=True, fill="both")

    def populate_analysis_combobox(self):
        try:
            controls = api_client.get_all_controls()
            self.controls_map = {c['name']: c['id'] for c in controls}
            if not controls:
                self.analysis_combobox.configure(values=["Aucun contrôle disponible"])
                self.analysis_combobox.set("Aucun contrôle disponible")
            else:
                self.analysis_combobox.configure(values=list(self.controls_map.keys()))
                self.analysis_combobox.set(list(self.controls_map.keys())[0])
        except Exception as e:
            self.analysis_combobox.configure(values=["Erreur de chargement"])
            self.analysis_combobox.set("Erreur de chargement")
            print(f"Erreur de chargement des contrôles: {e}")

    def has_permission(self, permission: Permission):
        return permission in ROLE_PERMISSIONS.get(self.user_role, set())

    def check_temporary_password(self):
        if self.user_data['is_temporary_password']:
            dialog = ChangePasswordDialog(self)
            self.wait_window(dialog)
            new_password = dialog.result
            
            if new_password:
                try:
                    api_client.update_password(self.user_data['id'], new_password)
                    self.user_data['is_temporary_password'] = False
                    messagebox.showinfo("Succès", "Mot de passe mis à jour.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Échec de la mise à jour du mot de passe: {e}")
                    self.exit_application()
            else:
                messagebox.showwarning("Avertissement", "Vous devez changer votre mot de passe pour continuer.")
                self.exit_application()

    def logout(self):
        self.destroy()
        self.login_window.deiconify()

    def exit_application(self):
        self.login_window.destroy()