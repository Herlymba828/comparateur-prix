#!/usr/bin/env python
"""
Script de diagnostic pour vérifier le port d'écoute de Gunicorn
"""
import os
import sys
import socket
import subprocess

def check_port_listening(port):
    """Vérifie si un port est en écoute"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def get_port_from_env():
    """Récupère le port depuis les variables d'environnement"""
    port = os.getenv('PORT')
    if port:
        try:
            return int(port)
        except ValueError:
            return None
    return None

def check_gunicorn_processes():
    """Vérifie les processus Gunicorn en cours"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.split('\n')
        gunicorn_lines = [line for line in lines if 'gunicorn' in line.lower()]
        return gunicorn_lines
    except Exception as e:
        return [f"Erreur lors de la vérification: {e}"]

def main():
    print("=" * 60)
    print("🔍 Diagnostic du Port Gunicorn")
    print("=" * 60)
    
    # 1. Vérifier la variable PORT
    port = get_port_from_env()
    if port:
        print(f"✅ Variable PORT définie: {port}")
    else:
        print("⚠️  Variable PORT non définie")
        print("   Railway devrait définir automatiquement PORT")
        port = 8080
        print(f"   Utilisation du port par défaut: {port}")
    
    # 2. Vérifier si le port est en écoute
    print(f"\n🔌 Vérification du port {port}...")
    if check_port_listening(port):
        print(f"✅ Le port {port} est en écoute")
    else:
        print(f"❌ Le port {port} n'est PAS en écoute")
        print("   Cela signifie que Gunicorn n'a pas démarré ou écoute sur un autre port")
    
    # 3. Vérifier les processus Gunicorn
    print(f"\n🔍 Processus Gunicorn:")
    processes = check_gunicorn_processes()
    if processes:
        for proc in processes:
            print(f"   {proc}")
    else:
        print("   Aucun processus Gunicorn trouvé")
    
    # 4. Vérifier les variables Railway
    print(f"\n🚂 Variables Railway:")
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    railway_project = os.getenv('RAILWAY_PROJECT_ID')
    print(f"   RAILWAY_ENVIRONMENT: {railway_env or 'non défini'}")
    print(f"   RAILWAY_PROJECT_ID: {railway_project or 'non défini'}")
    
    # 5. Recommandations
    print(f"\n💡 Recommandations:")
    if not port or port == 8080:
        print("   - Vérifiez que Railway a bien défini la variable PORT")
        print("   - Railway définit automatiquement PORT lors du déploiement")
    if not check_port_listening(port):
        print("   - Vérifiez les logs Railway pour voir si Gunicorn a démarré")
        print("   - Vérifiez que start.sh est exécuté correctement")
        print("   - Vérifiez que Gunicorn utilise bien --bind 0.0.0.0:$PORT")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

