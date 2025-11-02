# hyper_framework_client/ui/themed_treeview.py
from tkinter import ttk
import customtkinter as ctk

def style_treeview(widget_instance):
    """Applique un style au Treeview pour correspondre au thème de CustomTkinter."""
    style = ttk.Style()
    
    # Détecter le thème actuel de customtkinter
    current_theme = ctk.get_appearance_mode()
    
    if current_theme == "Dark":
        bg_color = "#2b2b2b"
        fg_color = "white"
        header_bg = "#343638"
        selected_bg = "#1f538d"
    else: # Light mode
        bg_color = "#ebebeb"
        fg_color = "black"
        header_bg = "#d6d6d6"
        selected_bg = "#3a7ebf"

    style.theme_use("default")

    # Style pour les en-têtes
    style.configure("Treeview.Heading",
                    background=header_bg,
                    foreground=fg_color,
                    relief="flat",
                    font=('CTkFont', 11, 'bold')) # Police augmentée
    style.map("Treeview.Heading",
              background=[('active', header_bg)])

    # Style pour le corps du Treeview
    style.configure("Treeview",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=bg_color,
                    borderwidth=0,
                    rowheight=28,  # Augmente la hauteur des lignes
                    font=('TkDefaultFont', 11)) # Augmente la police du contenu
    style.map('Treeview', background=[('selected', selected_bg)], foreground=[('selected', 'white')])

    widget_instance.tag_configure('oddrow', background=bg_color)
    # Si vous voulez des lignes alternées, décommentez et ajustez la couleur ci-dessous
    # if current_theme == "Dark":
    #     widget_instance.tag_configure('evenrow', background="#343638")
    # else:
    #     widget_instance.tag_configure('evenrow', background="#e0e0e0")