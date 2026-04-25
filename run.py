import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    print(f"\n🚀 {description}...")
    try:
        # Use shell=True for Windows compatibility with uv
        process = subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao {description.lower()}: {e}")
        return False

def main():
    print("="*60)
    print("⚡ MOTOR DE ESCOLHA WHATSAPP - PREFEITURA DO RIO")
    print("="*60)

    # 1. Sincronizar dependências
    if not run_command("uv sync", "Sincronizando dependências com uv"):
        sys.exit(1)

    # 2. Registrar Kernel do Jupyter
    run_command(
        'uv run python -m ipykernel install --user --name=desafio-whatsapp --display-name "Desafio WhatsApp DS"',
        "Registrando Kernel do Jupyter"
    )

    # 3. Rodar Streamlit
    print("\n🌐 Iniciando Dashboard Streamlit...")
    print("Aguarde a abertura automática no seu navegador.")
    print("-" * 60)
    
    try:
        # Streamlit run bloqueia a execução, então é o último comando
        subprocess.run("uv run streamlit run visualizar.py", shell=True)
    except KeyboardInterrupt:
        print("\n👋 Finalizando processo...")

if __name__ == "__main__":
    main()
