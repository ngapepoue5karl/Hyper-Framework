"""
Dialogues personnalisés pour l'application Hyper-Framework
"""
import customtkinter as ctk
from tkinter import messagebox


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


class WeekInputDialog(ctk.CTkToplevel):
    """
    Fenêtre de dialogue pour saisir la semaine de l'analyse (ex: S22).
    """
    def __init__(self, parent, control_name):
        super().__init__(parent)
        self.result = None
        self.control_name = control_name

        self.title("Semaine de l'Analyse")
        self.geometry("450x220")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Rend la fenêtre modale
        self.grab_set()
        self.transient(parent)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        title_label = ctk.CTkLabel(
            main_frame, 
            text=f"Contrôle : {control_name}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        instruction_label = ctk.CTkLabel(
            main_frame, 
            text="Veuillez indiquer la semaine de cette analyse\n(ex: S22 pour semaine 22)",
            font=ctk.CTkFont(size=12)
        )
        instruction_label.pack(pady=(0, 10))

        self.week_entry = ctk.CTkEntry(main_frame, placeholder_text="S22", width=300)
        self.week_entry.pack(pady=5)
        self.week_entry.focus()

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Valider", command=self._on_ok).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", fg_color="gray", command=self._on_cancel).pack(side="left", padx=10)

        # Lier la touche Entrée à la validation
        self.bind("<Return>", lambda event: self._on_ok())

    def _on_ok(self):
        week = self.week_entry.get().strip()
        if not week:
            messagebox.showwarning("Semaine vide", "Veuillez indiquer une semaine (ex: S22).", parent=self)
            return
        self.result = week
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
