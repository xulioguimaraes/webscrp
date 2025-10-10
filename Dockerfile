# ============================================
# Dockerfile para Academia Scraper
# ============================================
# Este Dockerfile cria uma imagem completa para rodar o robô 
# de scraping sem precisar instalar Python, Chrome ou 
# dependências na máquina host.

# 1. IMAGEM BASE
# Usa Python 3.12 slim (versão leve) como base
FROM python:3.12-slim

# 2. METADADOS DA IMAGEM
LABEL maintainer="seu-email@example.com"
LABEL description="Robô de scraping da Academia das Apostas Brasil"
LABEL version="2.0"

# 3. VARIÁVEIS DE AMBIENTE DO SISTEMA
# Define variáveis para o Selenium encontrar o Chrome/ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 4. INSTALAÇÃO DE DEPENDÊNCIAS DO SISTEMA
# Instala Chromium, ChromeDriver, cron e outras dependências necessárias
RUN apt-get update && apt-get install -y \
    # Navegador Chromium (Chrome open-source)
    chromium \
    # Driver do Chromium para Selenium
    chromium-driver \
    # Cron para agendamento de tarefas
    cron \
    # Utilitário para downloads
    curl \
    # Fontes necessárias para renderização
    fonts-liberation \
    # Bibliotecas adicionais para Chromium funcionar corretamente
    libnss3 \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxtst6 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    # Limpa cache do apt para reduzir tamanho da imagem
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. CONFIGURAÇÃO DO DIRETÓRIO DE TRABALHO
# Define /app como diretório padrão dentro do container
WORKDIR /app

# 6. CÓPIA E INSTALAÇÃO DAS DEPENDÊNCIAS PYTHON
# Copia o arquivo de dependências primeiro (aproveitamento de cache)
COPY requirements.txt .

# Instala as dependências Python sem cache (reduz tamanho)
RUN pip install --no-cache-dir -r requirements.txt

# 7. CÓPIA DOS ARQUIVOS DO PROJETO
# Copia todos os arquivos necessários para /app
COPY academia_scraper/ ./academia_scraper/
COPY academia_scraper_improved.py .
COPY install_and_run.sh .
COPY README.md .
COPY crontab /etc/cron.d/scraper-cron
COPY docker-entrypoint.sh /usr/local/bin/

# 8. CONFIGURAÇÃO DO CRON
# Define permissões corretas para o arquivo cron
RUN chmod 0644 /etc/cron.d/scraper-cron && \
    # Registra o crontab
    crontab /etc/cron.d/scraper-cron && \
    # Cria arquivo de log do cron
    touch /var/log/cron.log && \
    # Torna os scripts executáveis
    chmod +x install_and_run.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# 9. CRIAÇÃO DE DIRETÓRIOS AUXILIARES
# Cria diretórios para logs e dados (caso sejam necessários)
RUN mkdir -p /app/logs /app/data

# 10. VARIÁVEL DE AMBIENTE PARA API
# Define URL padrão da API (pode ser sobrescrita ao executar)
ENV API_URL=https://sportstips-mu.vercel.app/d

# 11. VARIÁVEL PARA EXECUÇÃO IMEDIATA (opcional)
# Se RUN_ON_START=true, executa o scraper imediatamente ao iniciar
ENV RUN_ON_START=false

# 12. COMANDO DE EXECUÇÃO PADRÃO
# Inicia o cron daemon que executará o scraper automaticamente
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

