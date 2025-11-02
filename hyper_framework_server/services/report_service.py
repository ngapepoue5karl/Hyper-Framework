#---> FICHIER FINAL ET COMPLET : hyper_framework_server/services/report_service.py

from datetime import datetime
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

class ReportGenerator:
    def generate_and_save_report(self, user_data, control_data, analysis_results, save_path):
        """
        Génère un rapport DOCX programmatiquement en utilisant python-docx.
        Aucun template externe n'est utilisé.
        """
        document = docx.Document()

        # --- Définir le style de base du document ---
        style = document.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)

        # --- En-tête du document ---
        document.add_heading("Rapport d'Analyse de Contrôle", level=0)
        
        p_date = document.add_paragraph()
        p_date.add_run('Date de génération : ').bold = True
        p_date.add_run(datetime.now().strftime('%d/%m/%Y à %H:%M:%S'))

        p_control = document.add_paragraph()
        p_control.add_run('Contrôle exécuté : ').bold = True
        p_control.add_run(control_data.get('name', 'N/A'))

        p_user = document.add_paragraph()
        p_user.add_run('Analyste : ').bold = True
        p_user.add_run(user_data.get('username', 'N/A'))
        
        document.add_page_break()

        # --- Corps du rapport (boucle sur les résultats d'analyse) ---
        if not analysis_results:
             document.add_paragraph("L'analyse n'a produit aucun résultat à afficher.")
        
        for section in analysis_results:
            # Titre de la section
            document.add_heading(section.get('title', 'Section de résultat'), level=1)

            # Statistiques résumées
            summary_stats = section.get('summary_stats', {})
            if summary_stats:
                document.add_heading('Statistiques Clés', level=2)
                for key, value in summary_stats.items():
                    p_stat = document.add_paragraph(style='List Bullet')
                    p_stat.add_run(f"{key}: ").bold = True
                    p_stat.add_run(str(value))
            
            # Tableau des données détaillées
            items = section.get('items', [])
            display_columns = section.get('display_columns', {})
            
            if items and display_columns:
                document.add_heading('Données Détaillées', level=2)
                
                # Création du tableau
                headers = list(display_columns.values())
                table = document.add_table(rows=1, cols=len(headers))
                table.style = 'Table Grid'
                table.autofit = True

                # Remplissage des en-têtes
                header_cells = table.rows[0].cells
                for i, header_text in enumerate(headers):
                    cell_paragraph = header_cells[i].paragraphs[0]
                    run = cell_paragraph.add_run(header_text)
                    run.bold = True
                    cell_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

                # Remplissage des données
                column_keys = list(display_columns.keys())
                for item in items:
                    row_cells = table.add_row().cells
                    for i, key in enumerate(column_keys):
                        row_cells[i].text = str(item.get(key, ''))
            
            document.add_paragraph() # Ajoute un espace après la section

        # --- Sauvegarde du document final ---
        try:
            document.save(save_path)
            return save_path
        except Exception as e:
            raise IOError(f"Impossible de sauvegarder le fichier de rapport : {e}")

report_service = ReportGenerator()