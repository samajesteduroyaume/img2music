import os
import subprocess
import sys

def main():
    # Configuration pour Hugging Face Spaces
    os.environ['STREAMLIT_SERVER_PORT'] = '7860'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Démarrer Streamlit avec les paramètres
    cmd = [
        'streamlit', 'run', 'app.py',
        '--server.port=7860',
        '--server.address=0.0.0.0',
        '--server.headless=true',
        '--server.enableCORS=false',
        '--server.enableXsrfProtection=false'
    ]
    
    try:
        subprocess.Popen(cmd).wait()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        sys.exit(0)

if __name__ == "__main__":
    main()
