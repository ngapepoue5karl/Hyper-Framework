from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
import json
import os
import re
import pandas as pd
from datetime import datetime

from ..services.report_service import report_service
from ..services.script_execution_engine import execute_script_from_file
from ..database.database import get_db
from ..services.logging_service import logging_service

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/execute-and-generate', methods=['POST'])
def execute_and_generate_report():
    user_data = json.loads(request.form.get('user_data', '{}'))
    username = user_data.get('username', 'unknown')
    control_id = request.form.get('control_id')
    control_data_for_log = {'control_id': control_id}

    try:
        if not control_id:
            return jsonify({'error': 'control_id manquant.'}), 400
        
        db = get_db()
        control_row = db.execute("SELECT * FROM controls WHERE id = ?", (control_id,)).fetchone()
        if not control_row:
            logging_service.log_action(username, 'REPORT_GENERATE', 'FAILURE', {**control_data_for_log, 'error': 'Control not found'})
            return jsonify({'error': 'Contrôle non trouvé.'}), 404

        control_data = dict(control_row)
        control_data_for_log['control_name'] = control_data['name']
        control_data['input_definitions'] = json.loads(control_data['input_definitions'])

        script_path = os.path.join(current_app.config['SCRIPTS_DIR'], control_data['script_filename'])
        inputs_dir = current_app.config['INPUTS_DIR']
        run_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        input_file_paths = {}

        for input_def in control_data['input_definitions']:
            key = input_def['key']
            if key not in request.files: return jsonify({'error': f"Fichier manquant: {key}"}), 400
            file = request.files[key]
            unique_filename = f"{run_timestamp}_{key}_{secure_filename(file.filename)}"
            saved_path = os.path.join(inputs_dir, unique_filename)
            file.save(saved_path)
            input_file_paths[key] = saved_path

        results_with_dfs = execute_script_from_file(script_path, input_file_paths, current_app.config['OUTPUTS_DIR'])
        
        analysis_results = []
        for result in results_with_dfs:
            if 'dataframe' in result and isinstance(result['dataframe'], pd.DataFrame):
                result['items'] = result['dataframe'].to_dict('records')
                del result['dataframe']
            analysis_results.append(result)

        safe_name = re.sub(r'[^\w\.-]', '_', control_data.get('name', 'analyse'))
        report_filename = f"Rapport_{safe_name}_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.docx"
        save_path = os.path.join(current_app.config['REPORTS_DIR'], report_filename)
        
        report_service.generate_and_save_report(
            user_data, control_data, analysis_results, save_path
        )
        
        logging_service.log_action(username, 'REPORT_GENERATE', 'SUCCESS', control_data_for_log)
        return jsonify({
            "message": "Rapport généré avec succès.",
            "report_filename": report_filename
        })

    except Exception as e:
        current_app.logger.error(f"Erreur de génération de rapport: {e}", exc_info=True)
        logging_service.log_action(username, 'REPORT_GENERATE', 'FAILURE', {**control_data_for_log, 'error': str(e)})
        return jsonify({'error': f"Une erreur inattendue est survenue: {str(e)}"}), 500


@bp.route('/download/<filename>', methods=['GET'])
def download_report(filename):
    username = request.args.get('username', 'unknown')
    try:
        response = send_from_directory(
            current_app.config['REPORTS_DIR'],
            filename,
            as_attachment=True
        )
        logging_service.log_action(username, 'REPORT_DOWNLOAD', 'SUCCESS', {'filename': filename})
        return response
    except FileNotFoundError:
        logging_service.log_action(username, 'REPORT_DOWNLOAD', 'FAILURE', {'filename': filename, 'error': 'File not found'})
        return jsonify({'error': 'Fichier rapport non trouvé.'}), 404