"""
Dialogues personnalisés pour l'application Hyper-Framework
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime


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


class PeriodInputDialog(ctk.CTkToplevel):
    """
    Fenêtre de dialogue générique pour saisir la période de l'analyse selon sa périodicité.
    Supporte: WEEK, MONTH, QUARTER, SEMESTER
    """
    def __init__(self, parent, control_name, periodicity='WEEK'):
        super().__init__(parent)
        self.result = None
        self.control_name = control_name
        self.periodicity = periodicity.upper()

        # Configuration selon la périodicité
        self.config = self._get_period_config()
        
        self.title(self.config['title'])
        self.geometry("500x280")
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
            text=self.config['instruction'],
            font=ctk.CTkFont(size=12)
        )
        instruction_label.pack(pady=(0, 15))

        self.period_entry = ctk.CTkEntry(
            main_frame, 
            placeholder_text=self.config['placeholder'], 
            width=350
        )
        self.period_entry.pack(pady=5)
        self.period_entry.focus()
        
        # Exemples supplémentaires
        examples_label = ctk.CTkLabel(
            main_frame,
            text=self.config['examples'],
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        examples_label.pack(pady=(5, 0))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Valider", command=self._on_ok).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", fg_color="gray", command=self._on_cancel).pack(side="left", padx=10)

        # Lier la touche Entrée à la validation
        self.bind("<Return>", lambda event: self._on_ok())

    def _get_period_config(self):
        """Retourne la configuration spécifique à chaque type de périodicité."""
        configs = {
            'WEEK': {
                'title': 'Semaine de l\'Analyse',
                'instruction': 'Veuillez indiquer la semaine de cette analyse',
                'placeholder': 'S22',
                'examples': 'Exemples : S22, S01, S52',
                'validation_msg': 'Veuillez indiquer une semaine (ex: S22 pour semaine 22).'
            },
            'MONTH': {
                'title': 'Mois de l\'Analyse',
                'instruction': 'Veuillez indiquer le mois de cette analyse',
                'placeholder': 'M03',
                'examples': 'Exemples : M03, M12',
                'validation_msg': 'Veuillez indiquer un mois (ex: M03 pour le mois de Mars).'
            },
            'QUARTER': {
                'title': 'Trimestre de l\'Analyse',
                'instruction': 'Veuillez indiquer le trimestre de cette analyse',
                'placeholder': 'T2',
                'examples': 'Exemples : T1, T2,...',
                'validation_msg': 'Veuillez indiquer un trimestre (ex: T2 pour le trimestre 2).'
            },
            'SEMESTER': {
                'title': 'Semestre de l\'Analyse',
                'instruction': 'Veuillez indiquer le semestre de cette analyse',
                'placeholder': 'S1',
                'examples': 'Exemples : S1, S2,...',
                'validation_msg': 'Veuillez indiquer un semestre (ex: S1 pour le semestre 1).'
            }
        }
        return configs.get(self.periodicity, configs['WEEK'])

    def _on_ok(self):
        period = self.period_entry.get().strip()
        if not period:
            messagebox.showwarning(
                "Période vide", 
                self.config['validation_msg'], 
                parent=self
            )
            return
        self.result = period
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


# Garder l'ancienne classe pour la compatibilité (alias)
class WeekInputDialog(PeriodInputDialog):
    """Alias pour la compatibilité avec l'ancien code."""
    def __init__(self, parent, control_name):
        super().__init__(parent, control_name, periodicity='WEEK')
