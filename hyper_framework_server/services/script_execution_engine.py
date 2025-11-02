#---> FICHIER MODIFIÉ : hyper_framework_server/services/script_execution_engine.py

import sys
import importlib.util
from pathlib import Path
import os

def execute_script_from_file(script_path: str, input_file_paths: dict, output_dir_path: str) -> list:
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

        return results

    except Exception as e:
        # En cas d'erreur dans le script, on la propage
        # Cela permet au handler d'API de la capturer et de retourner une erreur 500
        print(f"Erreur lors de l'exécution du script '{script_path}': {e}")
        raise e