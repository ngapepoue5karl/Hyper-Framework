#---> FICHIER MODIFIÉ : hyper_framework_server/api/analysis_routes.py

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import io
import json
import os
import re
import ast
from functools import wraps
from datetime import datetime
from ..database.database import get_db
from ..services.script_execution_engine import execute_script_from_file
from ..auth.roles import Role, Permission, ROLE_PERMISSIONS
from ..services.logging_service import logging_service
from ..services.security_service import analyze_code_security

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

def _parse_inputs_from_script(script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as f: return _parse_inputs_from_code_string(f.read())
    except FileNotFoundError: return []

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
    week_label = request.form.get('week_label', 'N/A')

    db = get_db()
    control = db.execute("SELECT name, script_filename, input_definitions FROM controls WHERE id = ?", (control_id,)).fetchone()
    if not control: 
        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'FAILURE', {'control_id': control_id, 'error': 'Control not found'})
        return jsonify({'error': 'Contrôle non trouvé.'}), 404
    
    control_name = control['name']
    
    try:
        script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control['script_filename'])
        run_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        inputs_dir = current_app.config['INPUTS_DIR']
        outputs_dir = current_app.config['OUTPUTS_DIR']
        input_file_paths = {}
        input_definitions = json.loads(control['input_definitions'])
        
        # Collecter les informations sur les fichiers chargés
        files_info = []
        
        for input_def in input_definitions:
            key = input_def['key']
            if key not in request.files: return jsonify({'error': f"Fichier manquant: {key}"}), 400
            file = request.files[key]
            safe_filename = secure_filename(file.filename)
            unique_filename = f"{run_timestamp}_{key}_{safe_filename}"
            saved_path = os.path.join(inputs_dir, unique_filename)
            file.save(saved_path)
            input_file_paths[key] = saved_path
            
            # Enregistrer les infos du fichier
            files_info.append({
                'key': key,
                'original_name': file.filename,
                'saved_name': unique_filename
            })
            
        results_with_dfs = execute_script_from_file(script_path, input_file_paths, outputs_dir)
        
        serialized_results = []
        for result in results_with_dfs:
            if 'dataframe' in result and isinstance(result['dataframe'], pd.DataFrame):
                result['items'] = result['dataframe'].to_dict('records')
                del result['dataframe']
            serialized_results.append(result)

        # Sauvegarder l'historique de l'analyse dans la base de données
        try:
            db.execute(
                """INSERT INTO analysis_runs 
                   (control_id, control_name, week_label, username, results_json, files_info) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (control_id, control_name, week_label, username, 
                 json.dumps(serialized_results), json.dumps(files_info))
            )
            db.commit()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")
            # On continue même si la sauvegarde échoue

        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'SUCCESS', {'control_id': control_id, 'control_name': control_name, 'week_label': week_label})
        return jsonify(serialized_results)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        logging_service.log_action(username, 'ANALYSIS_EXECUTE', 'FAILURE', {'control_id': control_id, 'control_name': control_name, 'error': str(e)})
        return jsonify({'error': f"Erreur serveur: {e}"}), 500

@bp.route('/results/<filename>', methods=['GET'])
def get_result_file(filename):
    try:
        return send_from_directory(current_app.config['OUTPUTS_DIR'], filename, as_attachment=False)
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
            with open(script_path, 'r', encoding='utf-8') as f: control_data['script_code'] = f.read()
        except FileNotFoundError:
            control_data['script_code'] = f"# ERREUR: Fichier '{control_data['script_filename']}' non trouvé."
        
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
            """SELECT id, control_id, control_name, week_label, username, executed_at 
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