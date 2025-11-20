"""
Script de migration pour réorganiser les fichiers d'analyse
Ancienne structure : data/inputs/ et data/outputs/
Nouvelle structure : data/save/[Contrôle]/[Contrôle Période]/Inputs/ et Outputs/
"""

import os
import shutil
import sys
from pathlib import Path

# Ajouter le chemin parent pour pouvoir importer config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def migrate_file_structure():
    """Migre les fichiers de l'ancienne structure vers la nouvelle"""
    
    # Chemins
    server_root = Path(__file__).resolve().parent.parent
    data_dir = server_root / "data"
    old_inputs_dir = data_dir / "inputs"
    old_outputs_dir = data_dir / "outputs"
    save_dir = data_dir / "save"
    
    print("=" * 60)
    print("MIGRATION DE LA STRUCTURE DES FICHIERS")
    print("=" * 60)
    print()
    
    # Vérifier si les anciens dossiers existent
    inputs_exists = old_inputs_dir.exists()
    outputs_exists = old_outputs_dir.exists()
    
    if not inputs_exists and not outputs_exists:
        print(" Les anciens dossiers 'inputs' et 'outputs' n'existent pas.")
        print("  Aucune migration nécessaire.")
        print()
        
        # Créer le nouveau dossier save s'il n'existe pas
        if not save_dir.exists():
            save_dir.mkdir(parents=True)
            print(f" Dossier 'save' créé : {save_dir}")
        else:
            print(f" Dossier 'save' existe déjà : {save_dir}")
        
        return
    
    print("Anciens dossiers détectés :")
    if inputs_exists:
        print(f"  - inputs : {old_inputs_dir}")
        input_files = list(old_inputs_dir.glob("*"))
        print(f"    ({len(input_files)} fichiers)")
    
    if outputs_exists:
        print(f"  - outputs : {old_outputs_dir}")
        output_files = list(old_outputs_dir.glob("*"))
        print(f"    ({len(output_files)} fichiers)")
    
    print()
    print("   ATTENTION : Cette migration va :")
    print("   1. Créer une structure de dossiers 'save' organisée par contrôle")
    print("   2. Les anciens fichiers seront conservés dans 'inputs' et 'outputs'")
    print("   3. Vous pourrez supprimer manuellement ces dossiers après vérification")
    print()
    
    response = input("Voulez-vous continuer ? (oui/non) : ").strip().lower()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("Migration annulée.")
        return
    
    print()
    print("-" * 60)
    print("Début de la migration...")
    print("-" * 60)
    print()
    
    # Créer le dossier save
    if not save_dir.exists():
        save_dir.mkdir(parents=True)
        print(f"✓ Dossier 'save' créé : {save_dir}")
    
    # Note importante pour l'utilisateur
    print()
    print(" NOTE IMPORTANTE :")
    print("   Les fichiers dans 'inputs' et 'outputs' utilisaient un format avec timestamp.")
    print("   Dans la nouvelle structure, chaque exécution d'analyse créera automatiquement")
    print("   ses propres dossiers organisés par contrôle et période.")
    print()
    print("   Les anciens fichiers restent dans 'inputs' et 'outputs' pour référence.")
    print("   Vous pouvez les supprimer manuellement une fois que vous avez vérifié")
    print("   que la nouvelle structure fonctionne correctement.")
    print()
    
    # Renommer les anciens dossiers pour sauvegarde
    if inputs_exists:
        backup_inputs = data_dir / "inputs_OLD_BACKUP"
        if backup_inputs.exists():
            shutil.rmtree(backup_inputs)
        shutil.move(str(old_inputs_dir), str(backup_inputs))
        print(f" Dossier 'inputs' renommé en 'inputs_OLD_BACKUP'")
    
    if outputs_exists:
        backup_outputs = data_dir / "outputs_OLD_BACKUP"
        if backup_outputs.exists():
            shutil.rmtree(backup_outputs)
        shutil.move(str(old_outputs_dir), str(backup_outputs))
        print(f" Dossier 'outputs' renommé en 'outputs_OLD_BACKUP'")
    
    print()
    print("=" * 60)
    print(" MIGRATION TERMINÉE AVEC SUCCÈS")
    print("=" * 60)
    print()
    print("Prochaines étapes :")
    print("  1. Lancez le serveur pour tester la nouvelle structure")
    print("  2. Exécutez quelques analyses pour vérifier que tout fonctionne")
    print("  3. Une fois satisfait, vous pouvez supprimer :")
    print(f"     - {data_dir / 'inputs_OLD_BACKUP'}")
    print(f"     - {data_dir / 'outputs_OLD_BACKUP'}")
    print()

if __name__ == "__main__":
    try:
        migrate_file_structure()
    except Exception as e:
        print()
        print(f" ERREUR lors de la migration : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
