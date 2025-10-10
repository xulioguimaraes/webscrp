#!/bin/bash
# ============================================
# Script de inicialização do container
# ============================================
# Este script é executado quando o container inicia

set -e

echo "🚀 Iniciando Academia Scraper com agendamento automático..."
echo "⏰ O scraper será executado todos os dias às 00:01"
echo "📍 Horário do container: $(date)"
echo "🌐 API configurada: $API_URL"
echo ""

# Cria diretórios necessários
mkdir -p /app/logs /app/data

# Substitui a variável API_URL no arquivo Python não é necessário,
# pois já está sendo passada como variável de ambiente

# Exibe a configuração do cron
echo "📅 Configuração do agendamento:"
cat /etc/cron.d/scraper-cron
echo ""

# Executa o scraper imediatamente na primeira vez (opcional)
if [ "$RUN_ON_START" = "true" ]; then
    echo "▶️  Executando scraper pela primeira vez..."
    cd /app && /usr/local/bin/python3 academia_scraper_improved.py
    echo ""
fi

# Cria o arquivo de log se não existir
touch /app/logs/cron.log

# Inicia o cron em foreground (para o container não finalizar)
echo "✅ Cron iniciado! Container em execução..."
echo "📊 Logs serão salvos em: /app/logs/cron.log"
echo "💡 Para ver os logs: docker-compose logs -f scraper"
echo ""

# Inicia o cron e mantém o container rodando
cron && tail -f /app/logs/cron.log

