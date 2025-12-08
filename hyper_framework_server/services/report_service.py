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
import matplotlib.patches as mpatches
import os
import tempfile
import re

class ReportGenerator:
    def _create_conclusion_hexagon(self, compliance_rate):
        """
        Crée un hexagone coloré selon le taux de conformité.
        
        Args:
            compliance_rate: Taux de conformité en pourcentage (0-100)
            
        Returns:
            Chemin vers l'image temporaire de l'hexagone
        """
        # Déterminer la couleur selon le taux
        if compliance_rate >= 95:
            color = '#4CAF50'  # Vert
        elif compliance_rate >= 50:
            color = '#FFC107'  # Jaune/Orange
        else:
            color = '#F44336'  # Rouge
        
        # Créer la figure
        fig, ax = plt.subplots(figsize=(0.5, 0.5), dpi=150)
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.axis('off')
        
        # Créer l'hexagone
        hexagon = mpatches.RegularPolygon(
            (0, 0),  # Centre
            6,  # Nombre de côtés
            radius=1,
            facecolor=color,
            edgecolor='black',
            linewidth=1
        )
        ax.add_patch(hexagon)
        
        # Sauvegarder dans un fichier temporaire
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        plt.savefig(temp_file.name, format='png', dpi=150, bbox_inches='tight', pad_inches=0)
        plt.close()
        
        return temp_file.name
    def _add_header_with_logo_and_table(self, document, control_name, control_code, analysis_results, control_metadata=None, execution_date=None):
        """
        Ajoute un en-tête avec :
        - Ligne 1 : Logo (gauche) | Titre centré | Code de contrôle (droite)
        - Ligne 2 : Tableau avec les informations du contrôle
        
        Args:
            control_metadata: Dictionnaire contenant les métadonnées du contrôle
            execution_date: Date d'exécution au format YYYYMMDD-HHMMSS
        """
        section = document.sections[0]
        header = section.header
        
        # Nettoyer l'en-tête existant
        for paragraph in header.paragraphs:
            paragraph.clear()
        
        # --- LIGNE 1 : Logo, Titre, Code ---
        # Créer un tableau à 3 colonnes pour la première ligne
        top_table = header.add_table(rows=1, cols=3, width=Inches(6.0))
        top_table.autofit = False
        top_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Ajuster les largeurs des colonnes
        top_table.columns[0].width = Inches(1.0)  # Logo
        top_table.columns[1].width = Inches(3.5)  # Titre
        top_table.columns[2].width = Inches(1.5)  # Code
        
        # Colonne 1 : Logo
        logo_cell = top_table.rows[0].cells[0]
        logo_para = logo_cell.paragraphs[0]
        
        # Chemin vers le logo
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets', 'images', 'logo_default.png'
        )
        
        if os.path.exists(logo_path):
            logo_run = logo_para.add_run()
            logo_run.add_picture(logo_path, width=Inches(0.8))
        else:
            # Fallback si le logo n'existe pas
            logo_para.add_run('LOGO')
        
        # Centrer verticalement le logo
        tc_logo = logo_cell._element
        tcPr_logo = tc_logo.get_or_add_tcPr()
        tcVAlign_logo = OxmlElement('w:vAlign')
        tcVAlign_logo.set(qn('w:val'), 'center')
        tcPr_logo.append(tcVAlign_logo)
        
        # Colonne 2 : Titre centré
        title_cell = top_table.rows[0].cells[1]
        title_para = title_cell.paragraphs[0]
        title_run = title_para.add_run(control_name)
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(14)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0, 0, 0)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement le titre
        tc_title = title_cell._element
        tcPr_title = tc_title.get_or_add_tcPr()
        tcVAlign_title = OxmlElement('w:vAlign')
        tcVAlign_title.set(qn('w:val'), 'center')
        tcPr_title.append(tcVAlign_title)
        
        # Colonne 3 : Code de contrôle avec date dynamique
        code_cell = top_table.rows[0].cells[2]
        code_para = code_cell.paragraphs[0]
        
        # Construire le code avec la date d'exécution
        if control_metadata and execution_date:
            control_code_prefix = control_metadata.get('control_code_prefix', control_code)
            # Extraire la date du timestamp (format: YYYYMMDD-HHMMSS)
            date_part = execution_date.split('-')[0]  # YYYYMMDD
            # Convertir en format YYYY_MM_DD
            formatted_date = f"{date_part[:4]}_{date_part[4:6]}_{date_part[6:8]}"
            full_control_code = f"{control_code_prefix}_{formatted_date}"
        else:
            full_control_code = control_code
        
        code_run = code_para.add_run(full_control_code)
        code_run.font.name = 'Arial'
        code_run.font.size = Pt(8)
        code_run.font.bold = True
        code_run.font.color.rgb = RGBColor(0, 0, 0)
        code_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement le code
        tc_code = code_cell._element
        tcPr_code = tc_code.get_or_add_tcPr()
        tcVAlign_code = OxmlElement('w:vAlign')
        tcVAlign_code.set(qn('w:val'), 'center')
        tcPr_code.append(tcVAlign_code)
        
        # Ajouter des bordures uniquement autour du tableau du haut (bordure externe)
        tbl_top = top_table._element
        tblPr_top = tbl_top.tblPr
        if tblPr_top is None:
            tblPr_top = OxmlElement('w:tblPr')
            tbl_top.insert(0, tblPr_top)
        
        tblBorders_top = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'right']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tblBorders_top.append(border)
        # Pas de bordure bottom pour le tableau du haut
        border_bottom = OxmlElement('w:bottom')
        border_bottom.set(qn('w:val'), 'none')
        border_bottom.set(qn('w:sz'), '0')
        tblBorders_top.append(border_bottom)
        # Supprimer les bordures internes verticales
        for border_name in ['insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'none')
            border.set(qn('w:sz'), '0')
            tblBorders_top.append(border)
        tblPr_top.append(tblBorders_top)
        
        # --- LIGNE 2 : Tableau des informations (directement attaché sans espace) ---
        info_table = header.add_table(rows=2, cols=6, width=Inches(6.0))
        info_table.autofit = False
        info_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Définir les en-têtes du tableau
        headers = [
            'Application concernée',
            'Couche concernée',
            'Référence du risque',
            'Nom du risque',
            'Conclusion',
            'Nom du contrôle'
        ]
        
        # Remplir les en-têtes
        header_cells = info_table.rows[0].cells
        for i, header_text in enumerate(headers):
            cell = header_cells[i]
            cell_para = cell.paragraphs[0]
            cell_run = cell_para.add_run(header_text)
            cell_run.font.name = 'Arial'
            cell_run.font.size = Pt(8)
            cell_run.font.bold = True
            cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Centrer verticalement
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcVAlign = OxmlElement('w:vAlign')
            tcVAlign.set(qn('w:val'), 'center')
            tcPr.append(tcVAlign)
        
        data_cells = info_table.rows[1].cells
        
        # Utiliser les métadonnées du contrôle si disponibles
        if control_metadata:
            application = control_metadata.get('application', 'N/A')
            layer = control_metadata.get('layer', 'N/A')
            risk_reference = control_metadata.get('risk_reference', 'N/A')
            risk_name = control_metadata.get('risk_name', 'N/A')
            control_name_meta = control_metadata.get('control_name', control_name)
        else:
            # Valeurs par défaut si pas de métadonnées
            application = 'N/A'
            layer = 'N/A'
            risk_reference = 'N/A'
            risk_name = 'N/A'
            control_name_meta = control_name
        
        # Calculer le taux de conformité pour la conclusion (hexagone)
        compliance_rate = 0
        if analysis_results and len(analysis_results) > 0:
            first_section = analysis_results[0]
            summary_stats = first_section.get('summary_stats', {})
            
            # Chercher le taux dans les statistiques
            for key, value in summary_stats.items():
                if 'taux' in key.lower() or 'conformité' in key.lower() or 'conformite' in key.lower():
                    # Extraire le nombre du pourcentage
                    if isinstance(value, str):
                        match = re.search(r'(\d+\.?\d*)', value)
                        if match:
                            compliance_rate = float(match.group(1))
                            break
                    elif isinstance(value, (int, float)):
                        compliance_rate = float(value)
                        break
        
        data_values = [
            application,
            layer,
            risk_reference,
            risk_name,
            None,  # Conclusion sera une image d'hexagone
            control_name_meta
        ]
        
        for i, value in enumerate(data_values):
            cell = data_cells[i]
            cell_para = cell.paragraphs[0]
            
            # Colonne 4 (index 4) = Conclusion avec hexagone
            if i == 4:
                try:
                    hexagon_path = self._create_conclusion_hexagon(compliance_rate)
                    cell_run = cell_para.add_run()
                    cell_run.add_picture(hexagon_path, width=Inches(0.25))
                    cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    # Nettoyer le fichier temporaire
                    try:
                        os.unlink(hexagon_path)
                    except:
                        pass
                except Exception as e:
                    print(f"Erreur lors de la création de l'hexagone: {e}")
                    # Fallback: afficher le taux en texte
                    cell_run = cell_para.add_run(f"{compliance_rate:.1f}%")
                    cell_run.font.name = 'Arial'
                    cell_run.font.size = Pt(7)
                    cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # Gérer les valeurs multilignes
            elif value is not None and '\n' in str(value):
                lines = str(value).split('\n')
                for j, line in enumerate(lines):
                    if j > 0:
                        cell_para = cell.add_paragraph()
                    cell_run = cell_para.add_run(line)
                    cell_run.font.name = 'Arial'
                    cell_run.font.size = Pt(7)
                    cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                cell_run = cell_para.add_run(str(value) if value is not None else '')
                cell_run.font.name = 'Arial'
                cell_run.font.size = Pt(7)
                cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Centrer verticalement
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcVAlign = OxmlElement('w:vAlign')
            tcVAlign.set(qn('w:val'), 'center')
            tcPr.append(tcVAlign)
        
        # Configurer les bordures du tableau d'informations (sans bordure top car lié au tableau du haut)
        tbl_info = info_table._element
        tblPr_info = tbl_info.tblPr
        if tblPr_info is None:
            tblPr_info = OxmlElement('w:tblPr')
            tbl_info.insert(0, tblPr_info)
        
        tblBorders_info = OxmlElement('w:tblBorders')
        # Pas de bordure top
        border_top = OxmlElement('w:top')
        border_top.set(qn('w:val'), 'none')
        border_top.set(qn('w:sz'), '0')
        tblBorders_info.append(border_top)
        # Bordures left, right, bottom, insideH, insideV
        for border_name in ['left', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tblBorders_info.append(border)
        # Pas de bordure bottom pour ce tableau
        border_bottom = OxmlElement('w:bottom')
        border_bottom.set(qn('w:val'), 'none')
        border_bottom.set(qn('w:sz'), '0')
        tblBorders_info.append(border_bottom)
        tblPr_info.append(tblBorders_info)
        
        # --- LIGNE 3 : Tableau du bas (Destinataire, Ref Description, PS3) ---
        bottom_table = header.add_table(rows=1, cols=3, width=Inches(6.0))
        bottom_table.autofit = False
        bottom_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        bottom_table.columns[0].width = Inches(3.2)
        bottom_table.columns[1].width = Inches(1.8)
        bottom_table.columns[2].width = Inches(1.0)
        
        # Cellule 1 : Destinataire
        dest_cell = bottom_table.rows[0].cells[0]
        dest_para = dest_cell.paragraphs[0]
        dest_run1 = dest_para.add_run('Destinataire : ')
        dest_run1.font.name = 'Arial'
        dest_run1.font.size = Pt(7)
        dest_run1.font.bold = True
        dest_run2 = dest_para.add_run('Tout le personnel de la direction des systèmes d\'informations')
        dest_run2.font.name = 'Arial'
        dest_run2.font.size = Pt(7)
        
        # Centrer verticalement
        tc_dest = dest_cell._element
        tcPr_dest = tc_dest.get_or_add_tcPr()
        tcVAlign_dest = OxmlElement('w:vAlign')
        tcVAlign_dest.set(qn('w:val'), 'center')
        tcPr_dest.append(tcVAlign_dest)
        
        # Cellule 2 : Ref Description (depuis métadonnées)
        ref_cell = bottom_table.rows[0].cells[1]
        ref_para = ref_cell.paragraphs[0]
        ref_run1 = ref_para.add_run('Ref Description : ')
        ref_run1.font.name = 'Arial'
        ref_run1.font.size = Pt(7)
        ref_run1.font.bold = True
        
        ref_description = 'N/A'
        if control_metadata:
            ref_description = control_metadata.get('ref_description', 'N/A')
        
        ref_run2 = ref_para.add_run(ref_description)
        ref_run2.font.name = 'Arial'
        ref_run2.font.size = Pt(7)
        
        # Centrer verticalement
        tc_ref = ref_cell._element
        tcPr_ref = tc_ref.get_or_add_tcPr()
        tcVAlign_ref = OxmlElement('w:vAlign')
        tcVAlign_ref.set(qn('w:val'), 'center')
        tcPr_ref.append(tcVAlign_ref)
        
        # Cellule 3 : Code supplémentaire
        ps_cell = bottom_table.rows[0].cells[2]
        ps_para = ps_cell.paragraphs[0]
        ps_run = ps_para.add_run('PS3_BC_SSI_FEN_3')
        ps_run.font.name = 'Arial'
        ps_run.font.size = Pt(7)
        ps_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_ps = ps_cell._element
        tcPr_ps = tc_ps.get_or_add_tcPr()
        tcVAlign_ps = OxmlElement('w:vAlign')
        tcVAlign_ps.set(qn('w:val'), 'center')
        tcPr_ps.append(tcVAlign_ps)
        
        # Configurer les bordures du tableau du bas (ferme le tableau complet)
        tbl_bottom = bottom_table._element
        tblPr_bottom = tbl_bottom.tblPr
        if tblPr_bottom is None:
            tblPr_bottom = OxmlElement('w:tblPr')
            tbl_bottom.insert(0, tblPr_bottom)
        
        tblBorders_bottom = OxmlElement('w:tblBorders')
        # Pas de bordure top car lié au tableau info
        border_top = OxmlElement('w:top')
        border_top.set(qn('w:val'), 'none')
        border_top.set(qn('w:sz'), '0')
        tblBorders_bottom.append(border_top)
        # Bordures left, right, bottom, insideV
        for border_name in ['left', 'right', 'bottom', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tblBorders_bottom.append(border)
        # Pas de insideH car une seule ligne
        border_insideH = OxmlElement('w:insideH')
        border_insideH.set(qn('w:val'), 'none')
        border_insideH.set(qn('w:sz'), '0')
        tblBorders_bottom.append(border_insideH)
        tblPr_bottom.append(tblBorders_bottom)
    
    def _add_signature_table(self, document):
        """
        Ajoute le tableau de signatures à la fin du rapport.
        
        Tableau avec 5 colonnes et 4 lignes :
        - Ligne 0 : [vide] | Rédaction | Révision | Révision | Approbation
        - Ligne 1 : Nom | [vide]  | Edward NANDA | Armel NGATCHUI | Blaise NDANGANG
        - Ligne 2 : Fonction | [vide] | POGR | RSSI | DSI
        - Ligne 3 : Date & Signature | [vide] | [vide] | [vide] | [vide]
        """
        # Ajouter un espace avant le tableau
        document.add_paragraph()
        
        # Créer le tableau 4 lignes x 5 colonnes
        table = document.add_table(rows=4, cols=5)
        table.style = 'Table Grid'
        table.autofit = False
        
        table.rows[0].cells[0].text = ''
        # Rédaction
        cell_redaction = table.rows[0].cells[1]
        p = cell_redaction.paragraphs[0]
        run = p.add_run('Rédaction')
        run.bold = True
        run.font.name = 'Arial'
        run.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell_redaction._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        # Révision (fusionner colonnes 2 et 3)
        cell_revision = table.rows[0].cells[2]
        cell_revision_next = table.rows[0].cells[3]
        cell_revision.merge(cell_revision_next)
        p = cell_revision.paragraphs[0]
        run = p.add_run('Révision')
        run.bold = True
        run.font.name = 'Arial'
        run.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell_revision._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:val'), 'center'
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        # Approbation
        cell_approbation = table.rows[0].cells[4]
        p = cell_approbation.paragraphs[0]
        run = p.add_run('Approbation')
        run.bold = True
        run.font.name = 'Arial'
        run.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell_approbation._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        
        # --- Ligne 1 : Noms ---
        # Label
        nom_label = table.rows[1].cells[0]
        nom_label.text = 'Nom'
        if nom_label.paragraphs and nom_label.paragraphs[0].runs:
            nom_label.paragraphs[0].runs[0].bold = True
            nom_label.paragraphs[0].runs[0].font.name = 'Arial'
            nom_label.paragraphs[0].runs[0].font.size = Pt(8)
        tc = nom_label._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        # Noms - Première cellule (Rédaction) vide pour remplissage manuel
        noms = ['', 'Edward NANDA', 'Armel NGATCHUI', 'Blaise NDANGANG']
        for i, nom in enumerate(noms, start=1):
            cell = table.rows[1].cells[i]
            cell.text = nom
            para = cell.paragraphs[0]
            for run in para.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(8)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcVAlign = OxmlElement('w:vAlign')
            tcVAlign.set(qn('w:val'), 'center')
            tcPr.append(tcVAlign)
        
        # --- Ligne 2 : Fonctions ---
        # Label
        fonction_label = table.rows[2].cells[0]
        fonction_label.text = 'Fonction'
        if fonction_label.paragraphs and fonction_label.paragraphs[0].runs:
            fonction_label.paragraphs[0].runs[0].bold = True
            fonction_label.paragraphs[0].runs[0].font.name = 'Arial'
            fonction_label.paragraphs[0].runs[0].font.size = Pt(8)
        tc = fonction_label._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        # Fonctions - Première cellule (Rédaction) vide pour remplissage manuel
        fonctions = ['', 'POGR', 'RSSI', 'DSI']
        for i, fonction in enumerate(fonctions, start=1):
            cell = table.rows[2].cells[i]
            cell.text = fonction
            para = cell.paragraphs[0]
            for run in para.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(8)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcVAlign = OxmlElement('w:vAlign')
            tcVAlign.set(qn('w:val'), 'center')
            tcPr.append(tcVAlign)
        
        # --- Ligne 3 : Date & Signature ---
        # Label
        date_label = table.rows[3].cells[0]
        date_label.text = 'Date & Signature'
        if date_label.paragraphs and date_label.paragraphs[0].runs:
            date_label.paragraphs[0].runs[0].bold = True
            date_label.paragraphs[0].runs[0].font.name = 'Arial'
            date_label.paragraphs[0].runs[0].font.size = Pt(8)
        tc = date_label._element
        tcPr = tc.get_or_add_tcPr()
        tcVAlign = OxmlElement('w:vAlign')
        tcVAlign.set(qn('w:val'), 'center')
        tcPr.append(tcVAlign)
        # Toutes les cellules Date & Signature restent vides pour remplissage manuel
        for i in range(1, 5):
            cell = table.rows[3].cells[i]
            cell.text = '\n\n\n'  # Espace pour la signature
            para = cell.paragraphs[0]
            for run in para.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(8)
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcVAlign = OxmlElement('w:vAlign')
            tcVAlign.set(qn('w:val'), 'center')
            tcPr.append(tcVAlign)
    
    def _add_footer_with_page_numbers(self, document):
        """
        Ajoute un bas de page avec un tableau à 3 colonnes et 2 lignes :
        - Colonne 1 : 2 cellules séparées (Version 1.4 / RESTREINT) avec bordures
        - Colonne 2 : Cellule fusionnée verticalement avec texte rouge
        - Colonne 3 : Cellule fusionnée verticalement avec numérotation
        """
        section = document.sections[0]
        footer = section.footer
        
        # Créer un tableau à 3 colonnes et 2 lignes
        footer_table = footer.add_table(rows=2, cols=3, width=Inches(6.5))
        footer_table.autofit = False
        
        # Ajuster les largeurs des colonnes
        footer_table.columns[0].width = Inches(1.5)
        footer_table.columns[1].width = Inches(3.7)
        footer_table.columns[2].width = Inches(1.3)
        
        # --- COLONNE 1 : Version 1.4 et RESTREINT (2 cellules séparées) ---
        version_cell = footer_table.rows[0].cells[0]
        version_para = version_cell.paragraphs[0]
        version_run = version_para.add_run('Version 1.4')
        version_run.font.name = 'Arial'
        version_run.font.size = Pt(8)
        version_run.font.bold = True
        version_run.font.color.rgb = RGBColor(0, 0, 0)  # Noir
        version_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_v = version_cell._element
        tcPr_v = tc_v.get_or_add_tcPr()
        tcVAlign_v = OxmlElement('w:vAlign')
        tcVAlign_v.set(qn('w:val'), 'center')
        tcPr_v.append(tcVAlign_v)
        
        restreint_cell = footer_table.rows[1].cells[0]
        restreint_para = restreint_cell.paragraphs[0]
        restreint_run = restreint_para.add_run('RESTREINT')
        restreint_run.font.name = 'Arial'
        restreint_run.font.size = Pt(8)
        restreint_run.font.bold = True
        restreint_run.font.color.rgb = RGBColor(0, 0, 0)  # Noir
        restreint_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_r = restreint_cell._element
        tcPr_r = tc_r.get_or_add_tcPr()
        tcVAlign_r = OxmlElement('w:vAlign')
        tcVAlign_r.set(qn('w:val'), 'center')
        tcPr_r.append(tcVAlign_r)
        
        # --- COLONNE 2 : Fusionner les 2 cellules verticalement ---
        center_cell_top = footer_table.rows[0].cells[1]
        center_cell_bottom = footer_table.rows[1].cells[1]
        center_cell_top.merge(center_cell_bottom)
        
        center_para = center_cell_top.paragraphs[0]
        center_run = center_para.add_run('Ce document est la propriété de Boissons du Cameroun')
        center_run.font.name = 'Arial'
        center_run.font.size = Pt(8)
        center_run.font.color.rgb = RGBColor(255, 0, 0)  # Rouge
        center_run.font.bold = False
        center_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Centrer verticalement
        tc_center = center_cell_top._element
        tcPr_center = tc_center.get_or_add_tcPr()
        tcVAlign_center = OxmlElement('w:vAlign')
        tcVAlign_center.set(qn('w:val'), 'center')
        tcPr_center.append(tcVAlign_center)
        
        # --- COLONNE 3 : Fusionner les 2 cellules verticalement ---
        right_cell_top = footer_table.rows[0].cells[2]
        right_cell_bottom = footer_table.rows[1].cells[2]
        right_cell_top.merge(right_cell_bottom)
        
        right_para = right_cell_top.paragraphs[0]
        right_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Ajouter "P a g e "
        page_text_run = right_para.add_run('P a g e ')
        page_text_run.font.name = 'Arial'
        page_text_run.font.size = Pt(8)
        page_text_run.font.bold = True
        page_text_run.font.color.rgb = RGBColor(128, 128, 128)  # Gris
        
        # Numéro de page actuel (en rouge)
        page_num_run = right_para.add_run()
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
        page_num_run.font.name = 'Arial'
        page_num_run.font.size = Pt(8)
        page_num_run.font.bold = True
        page_num_run.font.color.rgb = RGBColor(255, 0, 0)  # Rouge
        
        # Ajouter " sur "
        sur_run = right_para.add_run(' sur ')
        sur_run.font.name = 'Arial'
        sur_run.font.size = Pt(8)
        sur_run.font.bold = True
        sur_run.font.color.rgb = RGBColor(128, 128, 128)  # Gris
        
        # Nombre total de pages (en rouge)
        total_pages_run = right_para.add_run()
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
        total_pages_run.font.name = 'Arial'
        total_pages_run.font.size = Pt(8)
        total_pages_run.font.bold = True
        total_pages_run.font.color.rgb = RGBColor(255, 0, 0)  # Rouge
        
        # Centrer verticalement
        tc_right = right_cell_top._element
        tcPr_right = tc_right.get_or_add_tcPr()
        tcVAlign_right = OxmlElement('w:vAlign')
        tcVAlign_right.set(qn('w:val'), 'center')
        tcPr_right.append(tcVAlign_right)
        
        # --- Configurer les bordures du tableau ---
        tbl = footer_table._element
        tblPr = tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)
        
        # Bordures du tableau principal
        tblBorders = OxmlElement('w:tblBorders')
        
        # Seules les bordures de la colonne 1 sont visibles
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')  # Bordure fine
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')  # Noir
            tblBorders.append(border)
        tblPr.append(tblBorders)
        
        # Supprimer les bordures des cellules des colonnes 2 et 3
        for row in footer_table.rows:
            for i, cell in enumerate(row.cells):
                if i > 0:  # Colonnes 2 et 3
                    tcPr = cell._element.get_or_add_tcPr()
                    tcBorders = OxmlElement('w:tcBorders')
                    for border_name in ['top', 'left', 'bottom', 'right']:
                        border = OxmlElement(f'w:{border_name}')
                        border.set(qn('w:val'), 'none')
                        border.set(qn('w:sz'), '0')
                        border.set(qn('w:space'), '0')
                        border.set(qn('w:color'), 'auto')
                        tcBorders.append(border)
                    tcPr.append(tcBorders)

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
    
    def generate_and_save_report(self, user_data, control_data, analysis_results, save_path, period_label='N/A', control_metadata=None, execution_date=None):
        """
        Génère un rapport DOCX programmatiquement en utilisant python-docx.
        Inclut les graphiques générés avec matplotlib.
        
        Args:
            control_metadata: Métadonnées du contrôle définies dans le script
            execution_date: Date d'exécution au format YYYYMMDD-HHMMSS
        """
        document = docx.Document()
        temp_chart_files = []  # Pour nettoyer les fichiers temporaires

        try:
            # --- Définir le style de base du document ---
            style = document.styles['Normal']
            font = style.font
            font.name = 'Calibri'
            font.size = Pt(11)

            # --- Ajouter l'en-tête avec logo et tableau ---
            control_name = control_data.get('name', 'N/A')
            control_code = control_data.get('code', 'CTL_SSI_02_SAVE_2025_10_3')
            self._add_header_with_logo_and_table(
                document, 
                control_name, 
                control_code, 
                analysis_results,
                control_metadata=control_metadata,
                execution_date=execution_date
            )
            
            # --- Ajouter le bas de page ---
            self._add_footer_with_page_numbers(document)

            # --- NOUVELLE STRUCTURE DU CORPS DU RAPPORT ---
            
            # 1. Description du contrôle
            document.add_heading('Description du contrôle :', level=1)
            description_text = "N/A"
            if control_metadata and 'description' in control_metadata:
                description_text = control_metadata['description']
            p_desc = document.add_paragraph(description_text)
            p_desc.alignment = WD_ALIGN_PARAGRAPH.LEFT
            document.add_paragraph()  # Espace
            
            # 2. Analyse
            document.add_heading('Analyse :', level=1)
            analyse_text = "N/A"
            if control_metadata and 'analyse' in control_metadata:
                analyse_text = control_metadata['analyse']
            p_analyse = document.add_paragraph(analyse_text)
            p_analyse.alignment = WD_ALIGN_PARAGRAPH.LEFT
            document.add_paragraph()  # Espace
            
            # 3. Résultats
            document.add_heading('Résultats :', level=1)
            
            # --- Corps du rapport (boucle sur les résultats d'analyse) ---
            if not analysis_results:
                 document.add_paragraph("L'analyse n'a produit aucun resultat a afficher.")
            
            for section in analysis_results:
                # Titre de la section (niveau 2 car sous "Résultats")
                document.add_heading(section.get('title', 'Section de resultat'), level=2)

                # Statistiques résumées
                summary_stats = section.get('summary_stats', {})
                if summary_stats:
                    document.add_heading('Statistiques Cles', level=3)
                    for key, value in summary_stats.items():
                        p_stat = document.add_paragraph(style='List Bullet')
                        p_stat.add_run(f"{key}: ").bold = True
                        p_stat.add_run(str(value))
                
                # Graphiques (si présents)
                chart_configs = section.get('chart_configs', [])
                if chart_configs and summary_stats:
                    document.add_heading('Graphiques', level=3)
                    
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
                    document.add_heading('Donnees Detaillees', level=3)
                    
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

                    # Remplissage des données (limiter à 60 lignes pour éviter un rapport trop lourd)
                    max_rows = min(60, len(items))
                    for item in items[:max_rows]:
                        row_cells = table.add_row().cells
                        for i, key in enumerate(column_keys):
                            row_cells[i].text = str(item.get(key, ''))
                    
                    if len(items) > max_rows:
                        p_note = document.add_paragraph()
                        p_note.add_run(f"Note : Seules les {max_rows} premieres lignes sont affichees. ").italic = True
                        p_note.add_run(f"Total de {len(items)} lignes dans le fichier Excel complet.").italic = True
                
                document.add_paragraph()  # Ajoute un espace après la section
            
            # 4. Recommandations (vide - à remplir manuellement)
            document.add_paragraph()  # Espace supplémentaire
            document.add_heading('Recommandations :', level=1)
            document.add_paragraph()  # Espace vide pour remplissage manuel
            document.add_paragraph()  # Espace vide pour remplissage manuel
            document.add_paragraph()  # Espace vide pour remplissage manuel
            
            # 5. Évidence de suivi des exceptions (vide - à remplir manuellement)
            document.add_paragraph()  # Espace supplémentaire
            document.add_heading('Évidence de suivi des exceptions :', level=1)
            document.add_paragraph()  # Espace vide pour remplissage manuel
            document.add_paragraph()  # Espace vide pour remplissage manuel
            document.add_paragraph()  # Espace vide pour remplissage manuel
            
            # 6. Tableau de signatures
            document.add_page_break()  # Nouvelle page pour le tableau de signatures
            self._add_signature_table(document)

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