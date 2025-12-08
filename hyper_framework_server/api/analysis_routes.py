#---> FICHIER MODIFIÉ : hyper_framework_server/api/analysis_routes.py

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import io
import json
import os
import re
import ast
import zipfile
from functools import wraps
from datetime import datetime
from ..database.database import get_db
from ..services.script_execution_engine import execute_script_from_file
from ..auth.roles import Role, Permission, ROLE_PERMISSIONS
from ..services.logging_service import logging_service
from ..services.security_service import analyze_code_security
from ..services.chart_generator import generate_chart_specs

bp = Blueprint('analysis', __name__, url_prefix='/api')

def _sanitize_filename(name):
    name = name.lower(); name = re.sub(r'\s+', '_', name); name = re.sub(r'[^\w\.-]', '', name); return name
def _get_control_name_from_filename(filename):
    name = os.path.splitext(filename)[0]; name = name.replace('_', ' '); return ' '.join(word.capitalize() for word in name.split())

def _parse_inputs_from_code_string(code_string):
    try:
        tree = ast.parse(code_string)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__hyper_inputs__':
                        value = ast.literal_eval(node.value)
                        if isinstance(value, list): return value
    except (SyntaxError, ValueError): return []
    return []

def _parse_periodicity_from_code_string(code_string):
    """Extrait la périodicité définie dans __hyper_periodicity__.
    Par défaut retourne 'WEEK' si non défini.
    """
    try:
        tree = ast.parse(code_string)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__hyper_periodicity__':
                        value = ast.literal_eval(node.value)
                        if isinstance(value, str) and value in ['WEEK', 'MONTH', 'QUARTER', 'SEMESTER']:
                            return value
    except (SyntaxError, ValueError): 
        pass
    return 'WEEK'  # Valeur par défaut

def _parse_inputs_from_script(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as f: return _parse_inputs_from_code_string(f.read())
    except FileNotFoundError: return []

def _parse_periodicity_from_script(script_path):
    """Extrait la périodicité depuis un fichier de script."""
    try:
        with open(script_path, 'r', encoding='utf-8') as f: 
            return _parse_periodicity_from_code_string(f.read())
    except FileNotFoundError: 
        return 'WEEK'

def _sync_controls_with_filesystem():
    db = get_db(); scripts_dir = current_app.config['SCRIPTS_DIR']
    try: disk_filenames = {f for f in os.listdir(scripts_dir) if f.endswith('.py')}
    except FileNotFoundError: os.makedirs(scripts_dir); disk_filenames = set()
    db_controls = db.execute("SELECT id, script_filename FROM controls").fetchall(); db_filenames = {row['script_filename'] for row in db_controls}
    files_to_add = disk_filenames - db_filenames
    for filename in files_to_add:
        script_full_path = os.path.join(scripts_dir, filename)
        input_definitions = _parse_inputs_from_script(script_full_path)
        control_name = _get_control_name_from_filename(filename)
        if db.execute("SELECT id FROM controls WHERE name = ?", (control_name,)).fetchone(): control_name = f"{control_name} (Fichier: {filename})"
        db.execute("INSERT INTO controls (name, description, input_definitions, script_filename, last_updated_by) VALUES (?, ?, ?, ?, ?)", (control_name, "Contrôle auto-généré.", json.dumps(input_definitions), filename, "system-sync"))
    files_to_remove = db_filenames - disk_filenames
    if files_to_remove:
        placeholders = ','.join('?' for _ in files_to_remove)
        db.execute(f"DELETE FROM controls WHERE script_filename IN ({placeholders})", tuple(files_to_remove))
    db.commit()

def permission_required(permission: Permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json();
            if not data or 'username' not in data: return jsonify({'error': 'Authentification manquante.'}), 401
            username = data['username']; db = get_db(); user = db.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
            if not user: return jsonify({'error': 'Utilisateur non valide.'}), 401
            user_role = Role(user['role'])
            if permission not in ROLE_PERMISSIONS.get(user_role, set()): return jsonify({'error': 'Permission refusée.'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/controls/<int:control_id>/execute', methods=['POST'])
def execute_control(control_id):
    user_data = json.loads(request.form.get('user_data', '{}'))
    username = user_data.get('username', 'unknown')
    period_label = request.form.get('period_label', 'N/A')
    periodicity = request.form.get('periodicity', 'WEEK')

    db = get_db()
    control = db.execute("SELECT name, script_filename, input_definitions FROM controls WHERE id = ?", (control_id,)).fetchone()
    if not control: 
        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'FAILURE', {'control_id': control_id, 'error': 'Control not found'})
        return jsonify({'error': 'Contrôle non trouvé.'}), 404
    
    control_name = control['name']
    
    try:
        script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control['script_filename'])
        run_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Nouvelle structure de dossiers (simplifiée pour éviter les chemins trop longs)
        save_dir = current_app.config['SAVE_DIR']
        control_folder = os.path.join(save_dir, control_name)
        period_folder = os.path.join(control_folder, f"{control_name} {period_label}")
        inputs_dir = os.path.join(period_folder, "Inputs")
        outputs_dir = os.path.join(period_folder, "Outputs")
        
        # Créer les dossiers si nécessaire
        try:
            os.makedirs(inputs_dir, exist_ok=True)
            os.makedirs(outputs_dir, exist_ok=True)

        except Exception as e:
            print(f"Erreur lors de la création des dossiers: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f"Impossible de créer les dossiers: {e}"}), 500
        
        input_file_paths = {}
        input_definitions = json.loads(control['input_definitions'])
        
        # Collecter les informations sur les fichiers chargés
        files_info = []
        
        for input_def in input_definitions:
            key = input_def['key']
            if key not in request.files: return jsonify({'error': f"Fichier manquant: {key}"}), 400
            file = request.files[key]
            original_filename = file.filename
            # Extraire l'extension du fichier
            file_extension = os.path.splitext(original_filename)[1]
            # Utiliser un nom court pour éviter la limite de 260 caractères Windows
            # Format: clé + extension (ex: intune_file.csv au lieu de intune_file_DevicesWithInventory_UUID.csv)
            unique_filename = f"{key}{file_extension}"
            saved_path = os.path.join(inputs_dir, unique_filename)
            file.save(saved_path)
            input_file_paths[key] = saved_path
            
            # Enregistrer les infos du fichier (avec chemin relatif pour flexibilité)
            relative_path = os.path.join(control_name, period_label, "Inputs", unique_filename)
            files_info.append({
                'key': key,
                'original_name': file.filename,
                'saved_name': unique_filename,
                'relative_path': relative_path
            })
            
        results_with_dfs, control_metadata = execute_script_from_file(script_path, input_file_paths, outputs_dir)
        
        def convert_timestamps_to_strings(obj):
            """Convertit récursivement tous les Timestamps en strings pour la sérialisation JSON"""
            if isinstance(obj, pd.Timestamp):
                return obj.strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(obj) else None
            elif isinstance(obj, dict):
                return {k: convert_timestamps_to_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps_to_strings(item) for item in obj]
            elif pd.isna(obj):  # Gère les NaN, NaT, etc.
                return None
            return obj
        
        serialized_results = []
        for result in results_with_dfs:
            if 'dataframe' in result and isinstance(result['dataframe'], pd.DataFrame):
                # Convertir le DataFrame en dictionnaires
                records = result['dataframe'].to_dict('records')
                # Convertir tous les Timestamps en strings
                result['items'] = convert_timestamps_to_strings(records)
                del result['dataframe']
            
            # Générer les spécifications Vega-Lite si chart_configs est présent
            if 'chart_configs' in result and 'summary_stats' in result:
                try:
                    chart_specs = generate_chart_specs(
                        result['summary_stats'],
                        result['chart_configs']
                    )
                    result['chart_specs'] = chart_specs
                except Exception as e:
                    print(f"Erreur lors de la génération des graphiques: {e}")
                    # On continue sans les graphiques en cas d'erreur
                
            serialized_results.append(result)

        # Sauvegarder les résultats JSON dans le dossier Outputs
        try:
            # S'assurer que le dossier Outputs existe toujours
            os.makedirs(outputs_dir, exist_ok=True)
            results_json_path = os.path.join(outputs_dir, f"results_{run_timestamp}.json")
            with open(results_json_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_results, f, ensure_ascii=False, indent=2)
            
            # Chemin relatif pour la base de données
            relative_results_path = os.path.join(control_name, period_label, "Outputs", f"results_{run_timestamp}.json")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier JSON: {e}")
            relative_results_path = None

        # Sauvegarder l'historique de l'analyse dans la base de données
        run_id = None
        try:
            cursor = db.execute(
                """INSERT INTO analysis_runs 
                   (control_id, control_name, periodicity, period_label, username, results_json, files_info) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (control_id, control_name, periodicity, period_label, username, 
                 json.dumps(serialized_results), json.dumps(files_info))
            )
            run_id = cursor.lastrowid
            db.commit()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")
            # On continue même si la sauvegarde échoue

        # Génération automatique du rapport Word
        try:
            from ..services.report_service import report_service
            
            # S'assurer que le dossier Outputs existe toujours
            os.makedirs(outputs_dir, exist_ok=True)
            
            # Utiliser un nom de fichier court pour éviter la limite de 260 caractères Windows
            report_filename = f"Rapport_{period_label}_{run_timestamp}.docx"
            report_path = os.path.join(outputs_dir, report_filename)
            
            report_service.generate_and_save_report(
                user_data={'username': username},
                control_data={'name': control_name},
                analysis_results=serialized_results,
                save_path=report_path,
                period_label=period_label,
                control_metadata=control_metadata,
                execution_date=run_timestamp
            )
        except Exception as e:
            print(f"Erreur lors de la génération automatique du rapport Word: {e}")
            import traceback
            traceback.print_exc()
            # On continue même si la génération du rapport échoue

        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'SUCCESS', {
            'control_id': control_id, 
            'control_name': control_name, 
            'periodicity': periodicity, 
            'period_label': period_label,
            'outputs_dir': outputs_dir
        })
        # Retourner les résultats avec le run_id pour permettre le téléchargement du dossier
        return jsonify({
            'results': serialized_results,
            'run_id': run_id
        })
        
    except Exception as e:
        import traceback; traceback.print_exc()
        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'FAILURE', {'control_id': control_id, 'control_name': control_name, 'periodicity': periodicity, 'period_label': period_label, 'error': str(e)})
        return jsonify({'error': f"Erreur serveur: {e}"}), 500

@bp.route('/results/<path:filepath>', methods=['GET'])
def get_result_file(filepath):
    """Récupère un fichier de résultat avec son chemin relatif depuis save/"""
    try:
        save_dir = current_app.config['SAVE_DIR']
        full_path = os.path.join(save_dir, filepath)
        
        # Vérification de sécurité : s'assurer que le chemin reste dans save_dir
        if not os.path.abspath(full_path).startswith(os.path.abspath(save_dir)):
            return jsonify({'error': 'Accès non autorisé.'}), 403
            
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename, as_attachment=False)
    except FileNotFoundError:
        return jsonify({'error': 'Fichier de résultat non trouvé.'}), 404

@bp.route('/controls', methods=['GET'])
def get_all_controls():
    username = request.args.get('username', 'unknown')
    try: 
        _sync_controls_with_filesystem()
        db = get_db()
        rows = db.execute("SELECT id, name, description, updated_at, last_updated_by FROM controls ORDER BY name").fetchall()
        logging_service.log_action(username, 'VIEW_CONTROLS_LIST', 'SUCCESS', {'count': len(rows)})
        return jsonify([dict(row) for row in rows])
    except Exception as e: 
        logging_service.log_action(username, 'VIEW_CONTROLS_LIST', 'FAILURE', {'error': str(e)})
        return jsonify({'error': f"Erreur de sync: {e}"}), 500

@bp.route('/controls/<int:control_id>', methods=['GET'])
def get_control_details(control_id):
    username = request.args.get('username', 'unknown')
    db = get_db()
    try:
        row = db.execute("SELECT * FROM controls WHERE id = ?", (control_id,)).fetchone()
        if not row:
            logging_service.log_action(username, 'VIEW_CONTROL_DETAILS', 'FAILURE', {'control_id': control_id, 'error': 'Not found'})
            return jsonify({'error': 'Contrôle non trouvé.'}), 404
        
        control_data = dict(row)
        control_data['input_definitions'] = json.loads(control_data['input_definitions'])
        script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control_data['script_filename'])
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f: 
                script_code = f.read()
                control_data['script_code'] = script_code
                # Extraire la périodicité du script
                control_data['periodicity'] = _parse_periodicity_from_code_string(script_code)
        except FileNotFoundError:
            control_data['script_code'] = f"# ERREUR: Fichier '{control_data['script_filename']}' non trouvé."
            control_data['periodicity'] = 'WEEK'
        
        logging_service.log_action(username, 'VIEW_CONTROL_DETAILS', 'SUCCESS', {'control_id': control_id, 'control_name': control_data['name']})
        return jsonify(control_data)
    except Exception as e:
        control_name_row = db.execute("SELECT name FROM controls WHERE id = ?", (control_id,)).fetchone()
        control_name = control_name_row['name'] if control_name_row else 'N/A'
        logging_service.log_action(username, 'VIEW_CONTROL_DETAILS', 'FAILURE', {'control_id': control_id, 'control_name': control_name, 'error': str(e)})
        return jsonify({'error': str(e)}), 500

@bp.route('/controls', methods=['POST'])
@permission_required(Permission.MANAGE_CONTROLS)
def create_control():
    data = request.get_json()
    username = data.get('username', 'unknown')
    script_code = data.get('script_code', '')

    violations = analyze_code_security(script_code)
    if violations:
        error_details = ", ".join(violations)
        logging_service.log_action(username, 'CONTROL_CREATE_REJECTED', 'FAILURE', {'control_name': data.get('name'), 'violations': error_details})
        return jsonify({'error': 'Script rejeté pour raisons de sécurité', 'details': violations}), 400

    try:
        db = get_db()
        input_definitions = _parse_inputs_from_code_string(script_code)
        sanitized_name = _sanitize_filename(data['name'])
        base_filename, counter = f"{sanitized_name}.py", 1
        script_filename = base_filename
        script_path_base = current_app.config['SCRIPTS_DIR']
        while os.path.exists(os.path.join(script_path_base, script_filename)):
            script_filename = f"{sanitized_name}_{counter}.py"
            counter += 1
        script_path = os.path.join(script_path_base, script_filename)

        with open(script_path, 'w', encoding='utf-8') as f: f.write(script_code)
        
        db.execute("INSERT INTO controls (name, description, input_definitions, script_filename, last_updated_by) VALUES (?, ?, ?, ?, ?)", (data['name'], data['description'], json.dumps(input_definitions), script_filename, username))
        db.commit()
        
        logging_service.log_action(username, 'CONTROL_CREATE', 'SUCCESS', {'control_name': data['name']})
        return jsonify({"message": "Contrôle créé."}), 201
    except Exception as e:
        db.rollback()
        if 'script_path' in locals() and os.path.exists(script_path): os.remove(script_path)
        logging_service.log_action(username, 'CONTROL_CREATE', 'FAILURE', {'control_name': data.get('name'), 'error': str(e)})
        return jsonify({'error': str(e)}), 400

@bp.route('/controls/<int:control_id>', methods=['PUT'])
@permission_required(Permission.EDIT_CONTROLS)
def update_control(control_id):
    data = request.get_json()
    username = data.get('username', 'unknown')
    script_code = data.get('script_code', '')

    violations = analyze_code_security(script_code)
    if violations:
        error_details = ", ".join(violations)
        logging_service.log_action(username, 'CONTROL_UPDATE_REJECTED', 'FAILURE', {'control_id': control_id, 'violations': error_details})
        return jsonify({'error': 'Script rejeté pour raisons de sécurité', 'details': violations}), 400

    try:
        db = get_db()
        control_row = db.execute("SELECT script_filename, name FROM controls WHERE id = ?", (control_id,)).fetchone()
        if not control_row: return jsonify({'error': "Contrôle non trouvé."}), 404
        
        input_definitions = _parse_inputs_from_code_string(script_code)
        
        db.execute("UPDATE controls SET name = ?, description = ?, input_definitions = ?, last_updated_by = ?, updated_at = ? WHERE id = ?", (data['name'], data['description'], json.dumps(input_definitions), username, datetime.now(), control_id))
        
        script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control_row['script_filename'])
        with open(script_path, 'w', encoding='utf-8') as f: f.write(script_code)
        db.commit()
        
        logging_service.log_action(username, 'CONTROL_UPDATE', 'SUCCESS', {'control_id': control_id, 'new_name': data['name']})
        return jsonify({"message": "Contrôle mis à jour."})
    except Exception as e:
        db.rollback()
        logging_service.log_action(username, 'CONTROL_UPDATE', 'FAILURE', {'control_id': control_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 400

@bp.route('/controls/<int:control_id>', methods=['DELETE'])
@permission_required(Permission.DELETE_CONTROLS)
def delete_control(control_id):
    data = request.get_json()
    username = data.get('username', 'unknown')
    try:
        db = get_db()
        control_row = db.execute("SELECT script_filename, name FROM controls WHERE id = ?", (control_id,)).fetchone()
        control_name = control_row['name'] if control_row else 'N/A'
        db.execute("DELETE FROM controls WHERE id = ?", (control_id,))
        if control_row:
            script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control_row['script_filename'])
            if os.path.exists(script_path): os.remove(script_path)
        db.commit()
        logging_service.log_action(username, 'CONTROL_DELETE', 'SUCCESS', {'control_id': control_id, 'control_name': control_name})
        return '', 204
    except Exception as e:
        db.rollback()
        logging_service.log_action(username, 'CONTROL_DELETE', 'FAILURE', {'control_id': control_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 400


@bp.route('/analysis-runs', methods=['GET'])
def get_analysis_runs():
    """Récupère la liste de toutes les analyses exécutées"""
    username = request.args.get('username', 'unknown')
    try:
        db = get_db()
        rows = db.execute(
            """SELECT id, control_id, control_name, periodicity, period_label, username, executed_at 
               FROM analysis_runs 
               ORDER BY executed_at DESC"""
        ).fetchall()
        
        logging_service.log_action(username, 'VIEW_ANALYSIS_RUNS', 'SUCCESS', {'count': len(rows)})
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        logging_service.log_action(username, 'VIEW_ANALYSIS_RUNS', 'FAILURE', {'error': str(e)})
        return jsonify({'error': f"Erreur lors de la récupération de l'historique: {e}"}), 500


@bp.route('/analysis-runs/<int:run_id>', methods=['GET'])
def get_analysis_run_details(run_id):
    """Récupère les détails d'une analyse exécutée"""
    username = request.args.get('username', 'unknown')
    try:
        db = get_db()
        row = db.execute(
            """SELECT * FROM analysis_runs WHERE id = ?""",
            (run_id,)
        ).fetchone()
        
        if not row:
            logging_service.log_action(username, 'VIEW_ANALYSIS_RUN_DETAILS', 'FAILURE', {'run_id': run_id, 'error': 'Not found'})
            return jsonify({'error': 'Analyse non trouvée.'}), 404
        
        run_data = dict(row)
        
        # Désérialiser les JSON
        run_data['results_json'] = json.loads(run_data['results_json'])
        if run_data['files_info']:
            run_data['files_info'] = json.loads(run_data['files_info'])
        
        logging_service.log_action(username, 'VIEW_ANALYSIS_RUN_DETAILS', 'SUCCESS', {'run_id': run_id})
        return jsonify(run_data)
    except Exception as e:
        logging_service.log_action(username, 'VIEW_ANALYSIS_RUN_DETAILS', 'FAILURE', {'run_id': run_id, 'error': str(e)})
        return jsonify({'error': f"Erreur lors de la récupération des détails: {e}"}), 500


@bp.route('/analysis-runs/<int:run_id>/download-folder', methods=['GET'])
def download_analysis_folder(run_id):
    """Télécharge le répertoire complet d'un contrôle (Inputs + Outputs) sous forme de ZIP"""
    username = request.args.get('username', 'unknown')
    try:
        db = get_db()
        row = db.execute(
            """SELECT control_name, periodicity, period_label FROM analysis_runs WHERE id = ?""",
            (run_id,)
        ).fetchone()
        
        if not row:
            logging_service.log_action(username, 'DOWNLOAD_CONTROL_FOLDER', 'FAILURE', {'run_id': run_id, 'error': 'Not found'})
            return jsonify({'error': 'Analyse non trouvée.'}), 404
        
        control_name = row['control_name']
        period_label = row['period_label']
        
        # Construire le chemin du dossier du contrôle
        save_dir = current_app.config['SAVE_DIR']
        control_folder = os.path.join(save_dir, control_name)
        period_folder = os.path.join(control_folder, f"{control_name} {period_label}")
        
        if not os.path.exists(period_folder):
            logging_service.log_action(username, 'DOWNLOAD_CONTROL_FOLDER', 'FAILURE', {'run_id': run_id, 'error': 'Folder not found'})
            return jsonify({'error': 'Le répertoire du contrôle n\'existe pas.'}), 404
        
        # Créer un fichier ZIP en mémoire avec tout le contenu du dossier
        import io
        import zipfile
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Parcourir tous les fichiers et sous-dossiers
            for root, dirs, files in os.walk(period_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Créer un chemin relatif pour la structure dans le ZIP
                    arcname = os.path.relpath(file_path, period_folder)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        # Nom du fichier ZIP à télécharger
        zip_filename = f"{control_name}_{period_label}_complet.zip"
        zip_filename = re.sub(r'[^\w\.-]', '_', zip_filename)  # Nettoyer le nom
        
        logging_service.log_action(username, 'DOWNLOAD_CONTROL_FOLDER', 'SUCCESS', {'run_id': run_id, 'control_name': control_name, 'period_label': period_label})
        
        return (zip_buffer.getvalue(), 200, {
            'Content-Type': 'application/zip',
            'Content-Disposition': f'attachment; filename="{zip_filename}"'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging_service.log_action(username, 'DOWNLOAD_CONTROL_FOLDER', 'FAILURE', {'run_id': run_id, 'error': str(e)})
        return jsonify({'error': f"Erreur lors du téléchargement: {e}"}), 500