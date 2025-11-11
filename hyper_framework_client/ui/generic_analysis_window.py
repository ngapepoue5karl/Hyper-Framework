import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import re 
import datetime
import json
import threading
from ..api.api_client import api_client
from .themed_treeview import style_treeview

class GenericAnalysisFrame(ctk.CTkFrame):
    def __init__(self, master, app_parent, control_id, week_label):
        super().__init__(master)
        self.app_parent = app_parent
        self.control_id = control_id
        self.week_label = week_label
        
        self.file_paths = {}
        self.input_widgets = {}
        self.analysis_results_data = None 

        try:
            # L'utilisateur courant est nécessaire pour la journalisation
            username = app_parent.user_data['username']
            self.control_data = api_client.get_control_details(self.control_id, username)
        except Exception as e:
            messagebox.showerror("Erreur de Chargement", f"Impossible de charger les détails du contrôle:\n{e}", parent=self)
            self.destroy(); return
        
        self.user_data = self.app_parent.user_data
        self.create_widgets()

    def load_file(self, file_key):
        input_def = next((item for item in self.control_data['input_definitions'] if item["key"] == file_key), None)
        expected_format = input_def.get('format') if input_def else None
        file_types = [("Tous les fichiers", "*.*")]
        if expected_format: 
            file_types.insert(0, (f"Fichier {expected_format.upper()}", f"*.{expected_format}"))
        file_path = filedialog.askopenfilename(title=f"Sélectionnez '{input_def.get('label', file_key)}'", filetypes=file_types)
        if not file_path: return
        if expected_format and not file_path.lower().endswith(f".{expected_format.lower()}"):
            messagebox.showwarning("Format incorrect", f"Le format attendu est .{expected_format}", parent=self)
            return
        self.file_paths[file_key] = file_path
        filename = os.path.basename(file_path)
        self.input_widgets[file_key]['label'].configure(text=filename, text_color=("black", "white"))

    def run_analysis(self):
        if len(self.file_paths) != len(self.control_data['input_definitions']):
            return messagebox.showwarning("Fichiers manquants", "Veuillez charger tous les fichiers requis.", parent=self)

        # Nettoyer les résultats précédents
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Afficher la barre de progression
        progress_bar = ctk.CTkProgressBar(self.results_frame, mode='indeterminate')
        progress_bar.pack(pady=50, padx=20, fill='x')
        progress_bar.start()

        # Afficher un message d'information
        info_label = ctk.CTkLabel(self.results_frame, text="Analyse en cours, veuillez patienter...",
                                   font=ctk.CTkFont(size=14))
        info_label.pack(pady=10)

        self.update_idletasks()

        # Désactiver les boutons pendant l'exécution
        self.export_btn.configure(state='disabled')
        self.generate_report_btn.configure(state='disabled')

        # Préparer les fichiers à envoyer
        files_to_send = {}
        for key, path in self.file_paths.items():
            files_to_send[key] = (os.path.basename(path), open(path, 'rb'))

        data_payload = {
            'user_data': json.dumps(self.user_data),
            'week_label': self.week_label
        }

        # Fonction qui sera exécutée dans le thread
        def execute_analysis_thread():
            try:
                # Appel API qui peut prendre du temps
                final_results_data = api_client.execute_control(self.control_id, files_to_send, data_payload)

                # Mettre à jour l'interface dans le thread principal
                self.after(0, lambda: self._on_analysis_complete(final_results_data, progress_bar, info_label, files_to_send))

            except Exception as e:
                # Gérer les erreurs dans le thread principal
                self.after(0, lambda: self._on_analysis_error(str(e), progress_bar, info_label, files_to_send))

        # Lancer l'analyse dans un thread séparé
        analysis_thread = threading.Thread(target=execute_analysis_thread, daemon=True)
        analysis_thread.start()

    def _on_analysis_complete(self, final_results_data, progress_bar, info_label, files_to_send):
        """Appelée quand l'analyse est terminée avec succès"""
        try:
            progress_bar.stop()
            progress_bar.destroy()
            info_label.destroy()

            self.analysis_results_data = final_results_data
            self.export_btn.configure(state='normal')
            self.generate_report_btn.configure(state='normal')

            if not final_results_data:
                ctk.CTkLabel(self.results_frame, text="L'analyse s'est terminée sans retourner de résultat.").pack(pady=20)
            else:
                self.display_results(self.analysis_results_data)
        finally:
            # Fermer les fichiers
            for _, file_tuple in files_to_send.items():
                if file_tuple[1] and not file_tuple[1].closed:
                    file_tuple[1].close()

    def _on_analysis_error(self, error_message, progress_bar, info_label, files_to_send):
        """Appelée quand l'analyse échoue"""
        try:
            progress_bar.stop()
            progress_bar.destroy()
            info_label.destroy()
            messagebox.showerror("Erreur d'analyse", error_message, parent=self)
        finally:
            # Fermer les fichiers
            for _, file_tuple in files_to_send.items():
                if file_tuple[1] and not file_tuple[1].closed:
                    file_tuple[1].close()

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(side="top", fill="x", padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Affichage de la semaine en haut
        week_info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        week_info_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        
        ctk.CTkLabel(
            week_info_frame, 
            text=f"Semaine : {self.week_label}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left', padx=10)
        
        load_frame = ctk.CTkFrame(top_frame)
        load_frame.grid(row=1, column=0, sticky='ns', padx=(0, 10))
        ctk.CTkLabel(load_frame, text="1. Charger les fichiers", font=ctk.CTkFont(weight='bold')).grid(row=0, columnspan=2, pady=10)
        for i, input_def in enumerate(self.control_data['input_definitions']):
            key, label_text = input_def['key'], input_def['label']
            file_format = input_def.get('format')
            button = ctk.CTkButton(load_frame, text=f"Charger {label_text}", command=lambda k=key: self.load_file(k))
            button.grid(row=i+1, column=0, sticky='ew', pady=5, padx=10)
            status_text = f"Non chargé (.{file_format})" if file_format else "Non chargé"
            status_label = ctk.CTkLabel(load_frame, text=status_text, text_color="gray", width=200, anchor="w")
            status_label.grid(row=i+1, column=1, padx=10)
            self.input_widgets[key] = {'button': button, 'label': status_label}
        action_frame = ctk.CTkFrame(top_frame)
        action_frame.grid(row=1, column=2, sticky='ns', padx=10)
        ctk.CTkButton(action_frame, text="Lancer l'Analyse", command=self.run_analysis, height=40).pack(pady=10, fill='x', padx=10)
        self.export_btn = ctk.CTkButton(action_frame, text="Exporter (Excel)", command=self.export_results, state='disabled')
        self.export_btn.pack(pady=5, fill='x', padx=10)
        self.generate_report_btn = ctk.CTkButton(action_frame, text="Générer et Télécharger (DOCX)", command=self.generate_and_download_report, state='disabled')
        self.generate_report_btn.pack(pady=5, fill='x', padx=10)
        results_container = ctk.CTkFrame(self)
        results_container.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
        results_container.grid_rowconfigure(0, weight=1)
        results_container.grid_columnconfigure(0, weight=1)
        self.scrollable_results = ctk.CTkScrollableFrame(results_container, label_text=f"2. Résultats de l'Analyse - {self.control_data['name']}")
        self.scrollable_results.grid(row=0, column=0, sticky="nsew")
        self.results_frame = self.scrollable_results

    def display_results(self, results_data):
        for widget in self.results_frame.winfo_children(): widget.destroy()
        for section in results_data: self.create_result_section(self.results_frame, section)

    def create_result_section(self, parent, data):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10, padx=5)
        ctk.CTkLabel(frame, text=data.get('title', 'Section'), font=ctk.CTkFont(weight='bold')).pack(anchor='w', padx=10, pady=5)
        
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

            for i, (key, value) in enumerate(summary_stats.items()):
                stat_text = f"{key}: {value}"
                if key == "Taux":
                    # Afficher le Taux sur la deuxième ligne
                    ctk.CTkLabel(second_row_frame, text=stat_text, font=ctk.CTkFont(weight='bold')).pack(side='left', padx=15)
                else:
                    # Afficher les autres stats sur la première ligne
                    ctk.CTkLabel(first_row_frame, text=stat_text, font=ctk.CTkFont(weight='bold')).pack(side='left', padx=15)

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

            ysb = ctk.CTkScrollbar(tree_frame, command=tree.yview); ysb.grid(row=0, column=1, sticky='ns')
            xsb = ctk.CTkScrollbar(tree_frame, command=tree.xview, orientation="horizontal"); xsb.grid(row=1, column=0, sticky='ew')
            tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        else:
            ctk.CTkLabel(frame, text="Aucun élément à afficher.", font=ctk.CTkFont(slant='italic')).pack(padx=10, pady=10)

    def generate_and_download_report(self):
        if len(self.file_paths) != len(self.control_data['input_definitions']):
            return messagebox.showwarning("Fichiers manquants", "Veuillez charger tous les fichiers requis.", parent=self)
        self.generate_report_btn.configure(state='disabled', text="Génération en cours...")
        self.update_idletasks()
        files_to_send = {}
        generated_filename = None
        try:
            for key, path in self.file_paths.items():
                files_to_send[key] = (os.path.basename(path), open(path, 'rb'))
            data_payload = {
                'user_data': json.dumps(self.user_data),
                'week_label': self.week_label
            }
            response = api_client.execute_and_generate_report(self.control_id, files_to_send, data_payload)
            generated_filename = response.get('report_filename')
            if not generated_filename:
                raise Exception("Le serveur n'a pas retourné de nom de fichier pour le rapport.")
            save_path = filedialog.asksaveasfilename(
                initialfile=generated_filename,
                defaultextension=".docx",
                filetypes=[("Documents Word", "*.docx")],
                parent=self
            )
            if not save_path: return
            
            username = self.user_data['username']
            with api_client.download_report(generated_filename, username) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            messagebox.showinfo("Téléchargement Terminé", f"Le rapport a été sauvegardé avec succès:\n{save_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Erreur de Rapport", f"La génération ou le téléchargement du rapport a échoué : {e}", parent=self)
        finally:
            for _, file_tuple in files_to_send.items():
                if file_tuple[1] and not file_tuple[1].closed: 
                    file_tuple[1].close()
            self.generate_report_btn.configure(state='normal', text="Générer et Télécharger (DOCX)")


    def export_results(self):
        if not self.analysis_results_data: return messagebox.showwarning("Aucune donnée", "Veuillez lancer une analyse.", parent=self)
        safe_name = re.sub(r'[^\w\.-]', '_', self.control_data.get('name', 'analyse'))
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        default_filename = f"Resultats_{safe_name}_{timestamp}.xlsx"
        file_path = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".xlsx", filetypes=[("Fichiers Excel", "*.xlsx")], parent=self)
        if not file_path: return
        try:
            import pandas as pd
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for i, section in enumerate(self.analysis_results_data):
                    items = section.get('items', [])
                    display_columns = section.get('display_columns', [])
                    if not items or not display_columns: continue
                    
                    title = re.sub(r'[\\/*?:\[\]]', '', section.get('title', f'Resultat_{i+1}'))[:31]
                    
                    column_keys = [col['key'] for col in display_columns]
                    column_labels = {col['key']: col['label'] for col in display_columns}

                    df = pd.DataFrame(items)[column_keys].rename(columns=column_labels)
                    df.to_excel(writer, sheet_name=title, index=False)
            messagebox.showinfo("Succès", f"Fichier Excel exporté:\n{file_path}", parent=self)
        except Exception as e: messagebox.showerror("Erreur d'exportation", f"Une erreur est survenue :\n{e}", parent=self)