#---> NOUVEAU FICHIER : hyper_framework_server/services/security_service.py

import ast

# Listes noires pour la sécurité. Elles peuvent être étendues.
DANGEROUS_MODULES = {'subprocess', 'socket', 'sys', 'shutil', 'http'}
DANGEROUS_BUILTINS = {'eval', 'exec', 'compile', '__import__'}
DANGEROUS_ATTRIBUTES = {
    'system', 'popen', 'popen2', 'popen3', 'popen4', 'execl', 'execle', 'execlp', 
    'execv', 'execve', 'execvp', 'fork', 'kill', 'spawnl', 'spawnle', 'spawnlp', 
    'spawnv', 'spawnve', 'spawnvp', 'get_terminal_size', 'listdir', 'scandir', 
    'run', 'call', 'check_call', 'check_output'
}

class SecurityAnalyzer(ast.NodeVisitor):
    """
    Analyse un arbre syntaxique Python pour détecter des imports ou des appels
    potentiellement dangereux.
    """
    def __init__(self):
        self.violations = []
        # Pour suivre les alias (ex: import subprocess as sp)
        self.module_aliases = {}

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name
            if module_name in DANGEROUS_MODULES:
                self.violations.append(f"Importation du module dangereux '{module_name}' est interdite.")
            # Stocker l'alias pour une vérification ultérieure
            self.module_aliases[alias.asname or module_name] = module_name
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module_name = node.module
        if module_name in DANGEROUS_MODULES:
            self.violations.append(f"Importation depuis le module dangereux '{module_name}' est interdite.")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Vérifie les appels directs de fonctions natives dangereuses (ex: eval('...'))
        if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_BUILTINS:
            self.violations.append(f"Appel à la fonction native dangereuse '{node.func.id}' est interdit.")
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Vérifie les accès à des attributs dangereux (ex: os.system)
        if isinstance(node.value, ast.Name):
            variable_name = node.value.id
            attribute_name = node.attr
            
            # Retrouver le module original derrière un alias
            original_module = self.module_aliases.get(variable_name)

            if original_module in DANGEROUS_MODULES and attribute_name in DANGEROUS_ATTRIBUTES:
                self.violations.append(
                    f"Utilisation de l'attribut dangereux '{attribute_name}' "
                    f"du module '{original_module}' est interdite."
                )
        self.generic_visit(node)


def analyze_code_security(code_string: str) -> list:
    """
    Fonction principale pour analyser une chaîne de code Python.
    Retourne une liste de violations. Une liste vide signifie que le code est sûr.
    """
    try:
        tree = ast.parse(code_string)
        analyzer = SecurityAnalyzer()
        analyzer.visit(tree)
        return analyzer.violations
    except SyntaxError as e:
        return [f"Erreur de syntaxe dans le script : {e}"]