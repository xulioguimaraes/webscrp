#!/bin/bash

echo "🤖 Instalando dependências do Robô Academia das Apostas Brasil"
echo "=============================================================="

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale o Python3 primeiro."
    exit 1
fi

# Verifica se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale o pip3 primeiro."
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instala dependências
echo "📦 Instalando dependências Python..."
pip install selenium requests beautifulsoup4 webdriver-manager flask
pip install --upgrade lxml

# Instala ChromeDriver usando webdriver-manager
echo "🌐 Configurando ChromeDriver..."
python -c "
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Baixa e configura o ChromeDriver
driver_path = ChromeDriverManager().install()
print(f'ChromeDriver instalado em: {driver_path}')

# Testa se funciona
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.google.com')
    print('✅ ChromeDriver configurado com sucesso!')
    driver.quit()
except Exception as e:
    print(f'❌ Erro ao configurar ChromeDriver: {e}')
    exit(1)
"

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para executar o robô, use:"
echo "   source venv/bin/activate"
echo "   python academia_scraper_improved.py"
echo ""
echo "📝 Certifique-se de que sua API está rodando em localhost:8000"
echo "   ou configure a URL da API quando solicitado."
echo ""
echo "💡 Dica: Sempre ative o ambiente virtual antes de executar o robô!"
