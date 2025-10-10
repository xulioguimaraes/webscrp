#!/usr/bin/env python3
"""
Robô melhorado para extrair dados da Academia das Apostas Brasil
e cadastrar na API local

Este arquivo é o ponto de entrada do scraper.
O código foi refatorado e organizado em módulos separados.
"""

import os
from academia_scraper import AcademiaScraperImproved


def main():
    """Função principal"""
    print("🤖 Robô Academia das Apostas Brasil - Versão Melhorada")
    print("=" * 60)

    # Configurações
    # Verifica se API_URL foi definida como variável de ambiente (Docker)
    api_url = os.getenv('API_URL')
    
    if not api_url:
        # Modo interativo (local): pergunta ao usuário
        try:
            api_url = input(
                "Digite a URL da sua API (padrão: http://localhost:3000): ").strip()
        except EOFError:
            # Se não houver stdin disponível (ex: executando via cron/docker)
            api_url = ""
    
    # Define URL padrão se nada foi fornecido
    if not api_url:
        api_url = "http://localhost:3000"

    print(f"🌐 API configurada para: {api_url}")
    print("")

    # Executa o scraper
    scraper = AcademiaScraperImproved(api_url)
    scraper.run()


if __name__ == "__main__":
    main()
