#---> FICHIER MODIFIÉ : hyper_framework_server/services/report_service.py

from datetime import datetime
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement
from docx.oxml.ns import qn
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif
import matplotlib.pyplot as plt
import os
import tempfile
import re

class ReportGenerator:
    def _add_footer_with_page_numbers(self, document):
        """
        Ajoute un bas de page professionnel sur une ligne avec trois sections :
        - Gauche : Tableau 2 lignes avec Version 1.4 / RESTREINT
        - Centre : Ce document est la propriété de Boissons du Cameroun (en rouge)
        - Droite : Tableau 1 ligne avec Page X sur Y
        """
        section = document.sections[0]
        footer = section.footer
        
        # Créer un tableau principal à 3 colonnes sur 1 ligne
        footer_table = footer.add_table(rows=1, cols=3, width=Inches(6.5))
        footer_table.autofit = False
        
        # Ajuster les largeurs des colonnes
        footer_table.columns[0].width = Inches(1.8)
        footer_table.columns[1].width = Inches(3.0)
        footer_table.columns[2].width = Inches(1.7)
        
        cells = footer_table.rows[0].cells
        
        # --- GAUCHE : Sous-tableau Version/RESTREINT ---
        left_cell = cells[0]
        left_cell._element.clear_content()
        left_table = left_cell.add_table(rows=2, cols=1)
        left_table.style = 'Table Grid'
        
        # Ajuster la largeur du sous-tableau
        for row in left_table.rows:
            for cell in row.cells:
                cell.width = Inches(1.8)
        
        version_cell = left_table.rows[0].cells[0]
        version_para = version_cell.paragraphs[0]
        version_run = version_para.add_run('Version 1.4')
        version_run.font.size = Pt(10)
        version_run.font.bold = True
        version_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_v = version_cell._element
        tcPr_v = tc_v.get_or_add_tcPr()
        tcVAlign_v = OxmlElement('w:vAlign')
        tcVAlign_v.set(qn('w:val'), 'center')
        tcPr_v.append(tcVAlign_v)
        
        restreint_cell = left_table.rows[1].cells[0]
        restreint_para = restreint_cell.paragraphs[0]
        restreint_run = restreint_para.add_run('RESTREINT')
        restreint_run.font.size = Pt(10)
        restreint_run.font.bold = True
        restreint_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_r = restreint_cell._element
        tcPr_r = tc_r.get_or_add_tcPr()
        tcVAlign_r = OxmlElement('w:vAlign')
        tcVAlign_r.set(qn('w:val'), 'center')
        tcPr_r.append(tcVAlign_r)
        
        # --- CENTRE : Texte de propriété en rouge ---
        center_cell = cells[1]
        center_para = center_cell.paragraphs[0]
        center_run = center_para.add_run('Ce document est la propriété de Boissons du Cameroun')
        center_run.font.size = Pt(11)
        center_run.font.color.rgb = RGBColor(255, 0, 0)
        center_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_center = center_cell._element
        tcPr_center = tc_center.get_or_add_tcPr()
        tcVAlign_center = OxmlElement('w:vAlign')
        tcVAlign_center.set(qn('w:val'), 'center')
        tcPr_center.append(tcVAlign_center)
        
        # --- DROITE : Sous-tableau Page X sur Y ---
        right_cell = cells[2]
        # Supprimer le paragraphe par défaut
        right_cell._element.clear_content()
        
        right_table = right_cell.add_table(rows=1, cols=1)
        right_table.style = 'Table Grid'
        
        # Ajuster la largeur
        for row in right_table.rows:
            for cell in row.cells:
                cell.width = Inches(1.7)
        
        page_cell = right_table.rows[0].cells[0]
        page_para = page_cell.paragraphs[0]
        
        # Ajouter "Page "
        page_run = page_para.add_run('Page ')
        page_run.font.size = Pt(10)
        page_run.font.bold = True
        
        # Numéro de page actuel
        page_num_run = page_para.add_run()
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        page_num_run._r.append(fldChar1)
        
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = 'PAGE'
        page_num_run._r.append(instrText)
        
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        page_num_run._r.append(fldChar2)
        page_num_run.font.size = Pt(10)
        page_num_run.font.bold = True
        
        # Ajouter " sur "
        sur_run = page_para.add_run(' sur ')
        sur_run.font.size = Pt(10)
        sur_run.font.bold = True
        
        # Nombre total de pages
        total_pages_run = page_para.add_run()
        fldChar3 = OxmlElement('w:fldChar')
        fldChar3.set(qn('w:fldCharType'), 'begin')
        total_pages_run._r.append(fldChar3)
        
        instrText2 = OxmlElement('w:instrText')
        instrText2.set(qn('xml:space'), 'preserve')
        instrText2.text = 'NUMPAGES'
        total_pages_run._r.append(instrText2)
        
        fldChar4 = OxmlElement('w:fldChar')
        fldChar4.set(qn('w:fldCharType'), 'end')
        total_pages_run._r.append(fldChar4)
        total_pages_run.font.size = Pt(10)
        total_pages_run.font.bold = True
        
        page_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_page = page_cell._element
        tcPr_page = tc_page.get_or_add_tcPr()
        tcVAlign_page = OxmlElement('w:vAlign')
        tcVAlign_page.set(qn('w:val'), 'center')
        tcPr_page.append(tcVAlign_page)
        
        # Supprimer TOUTES les bordures du tableau principal
        tbl = footer_table._element
        tblPr = tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)
        
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'none')
            border.set(qn('w:sz'), '0')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tblBorders.append(border)
        tblPr.append(tblBorders)

    def _generate_chart_image(self, chart_config, summary_stats):
        """
        Génère une image de graphique à partir de chart_config et summary_stats.
        Retourne le chemin du fichier temporaire créé.
        """
        chart_type = chart_config.get('type')
        title = chart_config.get('title', 'Graphique')
        
        # Créer une nouvelle figure
        fig, ax = plt.subplots(figsize=(8, 5))
        
        try:
            if chart_type == 'bar':
                keys = chart_config.get('keys', [])
                colors = chart_config.get('colors', [])
                orientation = chart_config.get('orientation', 'vertical')
                
                values = [summary_stats.get(key, 0) for key in keys]
                # Convertir les pourcentages en float si nécessaire
                cleaned_values = []
                for v in values:
                    if isinstance(v, str) and '%' in v:
                        cleaned_values.append(float(v.replace('%', '')))
                    else:
                        cleaned_values.append(float(v) if v else 0)
                
                if orientation == 'horizontal':
                    ax.barh(keys, cleaned_values, color=colors if colors else None)
                    ax.set_xlabel('Valeur')
                else:
                    ax.bar(keys, cleaned_values, color=colors if colors else None)
                    ax.set_ylabel('Valeur')
                    plt.xticks(rotation=45, ha='right')
                
                ax.set_title(title, fontsize=14, fontweight='bold')
                plt.tight_layout()
                
            elif chart_type == 'pie':
                keys = chart_config.get('keys', [])
                colors = chart_config.get('colors', [])
                
                values = [summary_stats.get(key, 0) for key in keys]
                # Convertir les pourcentages en float si nécessaire
                cleaned_values = []
                for v in values:
                    if isinstance(v, str) and '%' in v:
                        cleaned_values.append(float(v.replace('%', '')))
                    else:
                        cleaned_values.append(float(v) if v else 0)
                
                ax.pie(cleaned_values, labels=keys, autopct='%1.1f%%', 
                       colors=colors if colors else None, startangle=90)
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.axis('equal')
                
            elif chart_type == 'gauge':
                key = chart_config.get('key')
                colors = chart_config.get('colors', ['#F44336', '#FF9800', '#4CAF50'])
                thresholds = chart_config.get('thresholds', [50, 80])
                max_value = chart_config.get('max_value', 100)
                
                value = summary_stats.get(key, 0)
                # Extraire le nombre du pourcentage si nécessaire
                if isinstance(value, str):
                    value = float(re.sub(r'[^0-9.]', '', value))
                else:
                    value = float(value)
                
                # Déterminer la couleur selon les seuils
                if value < thresholds[0]:
                    color = colors[0]
                elif value < thresholds[1]:
                    color = colors[1]
                else:
                    color = colors[2]
                
                # Créer un graphique en donut
                remainder = max_value - value
                values = [value, remainder]
                colors_chart = [color, '#E0E0E0']
                
                wedges, texts = ax.pie(values, colors=colors_chart, startangle=90,
                                      wedgeprops=dict(width=0.3))
                
                # Ajouter le texte au centre
                ax.text(0, 0, f'{value:.1f}%', ha='center', va='center',
                       fontsize=24, fontweight='bold')
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.axis('equal')
            
            # Sauvegarder dans un fichier temporaire
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
            
        except Exception as e:
            plt.close(fig)
            print(f"Erreur lors de la génération du graphique '{title}': {e}")
            return None
    
    def generate_and_save_report(self, user_data, control_data, analysis_results, save_path, period_label='N/A'):
        """
        Génère un rapport DOCX programmatiquement en utilisant python-docx.
        Inclut les graphiques générés avec matplotlib.
        """
        document = docx.Document()
        temp_chart_files = []  # Pour nettoyer les fichiers temporaires

        try:
            # --- Définir le style de base du document ---
            style = document.styles['Normal']
            font = style.font
            font.name = 'Calibri'
            font.size = Pt(11)

            # --- En-tête du document ---
            document.add_heading("Rapport d'Analyse de Controle", level=0)
            
            p_date = document.add_paragraph()
            p_date.add_run('Date de generation : ').bold = True
            p_date.add_run(datetime.now().strftime('%d/%m/%Y a %H:%M:%S'))

            p_control = document.add_paragraph()
            p_control.add_run('Controle execute : ').bold = True
            p_control.add_run(control_data.get('name', 'N/A'))
            
            p_period = document.add_paragraph()
            p_period.add_run('Periode : ').bold = True
            p_period.add_run(period_label)
            
            # --- Ajouter le bas de page ---
            self._add_footer_with_page_numbers(document)
            
            document.add_page_break()

            # --- Corps du rapport (boucle sur les résultats d'analyse) ---
            if not analysis_results:
                 document.add_paragraph("L'analyse n'a produit aucun resultat a afficher.")
            
            for section in analysis_results:
                # Titre de la section
                document.add_heading(section.get('title', 'Section de resultat'), level=1)

                # Statistiques résumées
                summary_stats = section.get('summary_stats', {})
                if summary_stats:
                    document.add_heading('Statistiques Cles', level=2)
                    for key, value in summary_stats.items():
                        p_stat = document.add_paragraph(style='List Bullet')
                        p_stat.add_run(f"{key}: ").bold = True
                        p_stat.add_run(str(value))
                
                # Graphiques (si présents)
                chart_configs = section.get('chart_configs', [])
                if chart_configs and summary_stats:
                    document.add_heading('Graphiques', level=2)
                    
                    for chart_config in chart_configs:
                        chart_path = self._generate_chart_image(chart_config, summary_stats)
                        if chart_path:
                            temp_chart_files.append(chart_path)
                            try:
                                # Ajouter le titre du graphique
                                p_chart_title = document.add_paragraph()
                                p_chart_title.add_run(chart_config.get('title', 'Graphique')).bold = True
                                p_chart_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                
                                # Ajouter l'image
                                document.add_picture(chart_path, width=Inches(5.5))
                                
                                # Centrer l'image
                                last_paragraph = document.paragraphs[-1]
                                last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                
                                document.add_paragraph()  # Espace après le graphique
                            except Exception as e:
                                print(f"Erreur lors de l'ajout du graphique au document: {e}")
                
                # Tableau des données détaillées
                items = section.get('items', [])
                display_columns = section.get('display_columns', {})
                
                if items and display_columns:
                    document.add_heading('Donnees Detaillees', level=2)
                    
                    # Création du tableau
                    if isinstance(display_columns, dict):
                        headers = list(display_columns.values())
                        column_keys = list(display_columns.keys())
                    else:
                        # Si display_columns est une liste de dicts avec 'key' et 'label'
                        headers = [col.get('label', col.get('key', '')) for col in display_columns]
                        column_keys = [col.get('key', '') for col in display_columns]
                    
                    table = document.add_table(rows=1, cols=len(headers))
                    table.style = 'Table Grid'
                    table.autofit = True

                    # Remplissage des en-têtes
                    header_cells = table.rows[0].cells
                    for i, header_text in enumerate(headers):
                        cell_paragraph = header_cells[i].paragraphs[0]
                        run = cell_paragraph.add_run(str(header_text))
                        run.bold = True
                        cell_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    # Remplissage des données (limiter à 50 lignes pour éviter un rapport trop lourd)
                    max_rows = min(50, len(items))
                    for item in items[:max_rows]:
                        row_cells = table.add_row().cells
                        for i, key in enumerate(column_keys):
                            row_cells[i].text = str(item.get(key, ''))
                    
                    if len(items) > max_rows:
                        p_note = document.add_paragraph()
                        p_note.add_run(f"Note : Seules les {max_rows} premieres lignes sont affichees. ").italic = True
                        p_note.add_run(f"Total de {len(items)} lignes dans le fichier Excel complet.").italic = True
                
                document.add_paragraph()  # Ajoute un espace après la section

            # --- Sauvegarde du document final ---
            document.save(save_path)
            
            return save_path
            
        except Exception as e:
            raise IOError(f"Impossible de sauvegarder le fichier de rapport : {e}")
        
        finally:
            # Nettoyer les fichiers temporaires de graphiques
            for temp_file in temp_chart_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Erreur lors de la suppression du fichier temporaire {temp_file}: {e}")

report_service = ReportGenerator()