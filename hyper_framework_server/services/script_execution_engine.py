#---> FICHIER MODIFIÉ : hyper_framework_server/services/script_execution_engine.py

import sys
import importlib.util
from pathlib import Path
import os

def execute_script_from_file(script_path: str, input_file_paths: dict, output_dir_path: str, inputs_dir_path: str = None) -> list:
    """
    Exécute un script Python de manière directe et synchrone.
    Le script est importé dynamiquement et sa fonction 'run' est appelée.
    """
    try:
        script_path_obj = Path(script_path)
        if not script_path_obj.exists():
            raise FileNotFoundError(f"Le fichier de script n'a pas été trouvé : {script_path}")

        # Crée un nom de module unique pour éviter les conflits de cache
        module_name = f"dynamic_script_{script_path_obj.stem}_{os.getpid()}"
        
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None:
            raise ImportError(f"Impossible de créer la spécification pour le module : {script_path}")
        
        analysis_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = analysis_module
        spec.loader.exec_module(analysis_module)

        if not hasattr(analysis_module, 'run'):
            raise AttributeError(f"Le script '{script_path_obj.name}' doit définir une fonction 'run(...)'.")

        results = analysis_module.run(input_file_paths, output_dir_path)
        
        if not isinstance(results, list):
             raise TypeError("La fonction 'run' du script doit retourner une liste.")

        # Ajouter les configurations de graphiques si elles existent
        if hasattr(analysis_module, '__hyper_charts__'):
            chart_configs = getattr(analysis_module, '__hyper_charts__')
            
            # Traiter chaque graphique et l'assigner à la section appropriée
            for chart_config in chart_configs:
                section_index = chart_config.get('section_index')
                
                if section_index is not None and 0 <= section_index < len(results):
                    # Ajouter ce graphique spécifique à la section désignée
                    result_section = results[section_index]
                    if 'summary_stats' in result_section:
                        # Créer la liste chart_configs si elle n'existe pas
                        if 'chart_configs' not in result_section:
                            result_section['chart_configs'] = []
                        # Ajouter seulement ce graphique (sans le section_index pour éviter confusion)
                        chart_config_copy = {k: v for k, v in chart_config.items() if k != 'section_index'}
                        result_section['chart_configs'].append(chart_config_copy)
                else:
                    # Si section_index n'est pas spécifié, comportement par défaut (tous les graphiques à la première section)
                    for result_section in results:
                        if 'summary_stats' in result_section:
                            if 'chart_configs' not in result_section:
                                result_section['chart_configs'] = chart_configs
                            break
        
        # Extraire les métadonnées du contrôle si elles existent
        control_metadata = None
        if hasattr(analysis_module, '__hyper_control_metadata__'):
            control_metadata = getattr(analysis_module, '__hyper_control_metadata__')

        return results, control_metadata

    except Exception as e:
        # En cas d'erreur dans le script, on la propage
        # Cela permet au handler d'API de la capturer et de retourner une erreur 500
        print(f"Erreur lors de l'exécution du script '{script_path}': {e}")
        raise e