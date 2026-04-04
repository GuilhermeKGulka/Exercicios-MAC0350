import os
import subprocess
import sys
import zipfile
import urllib.request
from pathlib import Path

def run_command(command, shell=False):
    """Executa um comando no terminal e exibe a saída."""
    print(f"🚀 Executando: {command}")
    result = subprocess.run(command, shell=shell, check=True)
    return result

def main():
    # 1. Criar Ambiente Virtual (.venv)
    if not os.path.exists(".venv"):
        print("📦 Criando ambiente virtual...")
        run_command([sys.executable, "-m", "venv", ".venv"])
    
    python_venv = ".venv/bin/python"
    pip_venv = ".venv/bin/pip"

    # 2. Instalar Requirements
    if os.path.exists("requirements.txt"):
        print("📥 Instalando dependências...")
        run_command([pip_venv, "install", "-r", "requirements.txt"])
    else:
        print("⚠️ requirements.txt não encontrado. Pulando instalação.")

    # 3. Configurar User-Agent (env.txt)
    if not os.path.exists("env.txt"):
        user_agent = input("📧 Digite seu email para o User-Agent (ex: seu@email.com): ")
        with open("env.txt", "w") as f:
            f.write(f"USER_AGENT=ProjetoEducacionalAnimaisDoBrasil/1.0 ({user_agent})")
        print("✅ Arquivo env.txt criado.")

    # 4. Download da Base de Dados (CTFB)
    url = "https://ipt.jbrj.gov.br/jbrj/archive.do?r=catalogo_taxonomico_da_fauna_do_brasil&v=1.50"
    zip_path = "ctfb_data.zip"
    extract_path = Path("ctfb")
    
    if not extract_path.exists():
        print("🌍 Baixando base de dados do CTFB (isso pode demorar)...")
        urllib.request.urlretrieve(url, zip_path)
        
        print("📂 Extraindo arquivos necessários...")
        extract_path.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extrair apenas os arquivos que precisamos
            for file in ["taxon.txt", "vernacularname.txt"]:
                zip_ref.extract(file, extract_path)
        
        os.remove(zip_path) # Limpar o zip
        print("✅ Dados extraídos para a pasta /ctfb.")

    # 5. Rodar o Importador
    if os.path.exists("import_ctfb.py"):
        print("🗄️ Iniciando importação para o banco de dados...")
        run_command([python_venv, "import_ctfb.py"])
    else:
        print("❌ Erro: import_ctfb.py não encontrado!")
        return

    # 6. Rodar o Servidor
    print("🔥 Setup concluído! Iniciando servidor FastAPI...")
    try:
        run_command([python_venv, "-m", "fastapi", "dev", "main.py"])
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")

if __name__ == "__main__":
    main()