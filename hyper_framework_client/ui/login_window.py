# hyper_framework_client/ui/login_window.py
import customtkinter as ctk
from tkinter import messagebox
from ..api.api_client import api_client
from .main_window import MainWindow

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hyper-Framework - Connexion")
        self.geometry("450x380")
        self.resizable(False, False)

        # Centrer la fenêtre
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")

        title_label = ctk.CTkLabel(main_frame, text="Connexion", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 25), padx=20)

        ctk.CTkLabel(main_frame, text="Nom d'utilisateur").pack(pady=(10, 5), padx=20, anchor="w")
        self.username_entry = ctk.CTkEntry(main_frame, width=300, height=35)
        self.username_entry.pack(pady=5, padx=20)

        ctk.CTkLabel(main_frame, text="Mot de passe").pack(pady=(10, 5), padx=20, anchor="w")
        self.password_entry = ctk.CTkEntry(main_frame, show="*", width=300, height=35)
        self.password_entry.pack(pady=5, padx=20)

        # --- MODIFICATION DU BOUTON (selon la nouvelle demande) ---
        # On garde la largeur par défaut mais on augmente la hauteur.
        login_button = ctk.CTkButton(main_frame, text="Se connecter", command=self.attempt_login, height=50) # Hauteur augmentée
        login_button.pack(pady=(30, 20), padx=20) # 'fill' a été retiré pour garder la largeur par défaut
        # --- FIN DE LA MODIFICATION ---

        self.username_entry.focus()
        self.bind('<Return>', lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Erreur", "Tous les champs sont requis.")
            return
        try:
            user_data = api_client.login(username, password)
            self.withdraw()  # On cache la fenêtre de connexion
            main_app = MainWindow(self, user_data)
            main_app.protocol("WM_DELETE_WINDOW", self.quit) # Si la fenêtre principale est fermée, on quitte tout
        except Exception as e:
            messagebox.showerror("Erreur de connexion", str(e))