import os
import subprocess
import sys
import zipfile
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CTFB_DIR = BASE_DIR / "ctfb"
VENV_DIR = BASE_DIR / ".venv"

def run_command(command, shell=False):
    """Executa um comando no terminal e exibe a saída."""
    print(f"🚀 Executando: {command}")
    result = subprocess.run(command, shell=shell, check=True, cwd=BASE_DIR)
    return result

def main():
    os.chdir(BASE_DIR)

    # 1. Criar Ambiente Virtual (.venv)
    if not VENV_DIR.exists():
        print("📦 Criando ambiente virtual...")
        run_command([sys.executable, "-m", "venv", ".venv"])
    
    python_venv = str(VENV_DIR / "bin" / "python")
    pip_venv = str(VENV_DIR / "bin" / "pip")

    # 2. Instalar Requirements
    if os.path.exists("requirements.txt"):
        print("📥 Instalando dependências...")
        run_command([pip_venv, "install", "-r", "requirements.txt"])
    else:
        print("⚠️ requirements.txt não encontrado. Pulando instalação.")

    # 3. Configurar User-Agent (env.txt)
    if not os.path.exists("env.txt"):
        user_agent = input("📧 Digite seu email para ser usado como User-Agent na API da wikimedia (ex: seu@email.com): ")
        with open("env.txt", "w") as f:
            f.write(f"USER_AGENT=ProjetoEducacionalAnimaisDoBrasil/1.0 ({user_agent})")
        print("✅ Arquivo env.txt criado.")

    # 4. Download da Base de Dados (CTFB)
    url = "https://ipt.jbrj.gov.br/jbrj/archive.do?r=catalogo_taxonomico_da_fauna_do_brasil&v=1.50"
    zip_path = BASE_DIR / "ctfb_data.zip"
    
    if not CTFB_DIR.exists():
        print("🌍 Baixando base de dados do CTFB...")
        urllib.request.urlretrieve(url, zip_path)
        
        print("📂 Extraindo arquivos necessários...")
        CTFB_DIR.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extrair apenas os arquivos que precisamos
            for file in ["taxon.txt", "vernacularname.txt"]:
                zip_ref.extract(file, CTFB_DIR)
        
        os.remove(zip_path) # Limpar o zip
        print("✅ Dados extraídos para a pasta /ctfb.")

    # 5. Rodar o Importador
    import_script = BASE_DIR / "scripts" / "import_ctfb.py"
    if import_script.exists():
        print("🗄️ Iniciando importação para o banco de dados...")
        run_command([python_venv, "scripts/import_ctfb.py"])

    # 6. Rodar o Servidor
    print("🔥 Setup concluído! Iniciando servidor FastAPI...")
    try:
        run_command([python_venv, "-m", "fastapi", "dev", "main.py"])
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")

if __name__ == "__main__":
    main()