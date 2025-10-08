#!/bin/bash

echo "🤖 Executando Robô Academia das Apostas Brasil"
echo "=============================================="

# Verifica se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Execute primeiro: ./install_and_run.sh"
    exit 1
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Executa o scraper
echo "🚀 Iniciando o robô..."
python academia_scraper_improved.py
