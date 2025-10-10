"""
Text extraction and processing utilities
"""

import re
from datetime import datetime
from typing import Optional


def is_match_finished(text: str) -> bool:
    """Verifica se a partida já terminou baseado no texto"""
    text_lower = text.lower()
    
    # Se contém "ao vivo" ou "live", definitivamente NÃO está terminada
    if 'ao vivo' in text_lower or 'live' in text_lower:
        return False
    
    # Palavras-chave que indicam que a partida já terminou ou foi adiada
    finished_keywords = [
        'terminado',
        'finalizado',
        'encerrado',
        'finished',
        'ended',
        'adiado',
        'adiada',
        'postponed',
        'cancelado',
        'cancelada',
        'cancelled',
        'canceled',
        'completed',
        'ft',  # Full Time
    ]
    
    # Verifica se contém alguma palavra-chave de partida terminada
    for keyword in finished_keywords:
        if keyword in text_lower:
            return True
    
    return False


def determine_category(text: str) -> str:
    """Determina a categoria do esporte baseada no texto"""
    text_lower = text.lower()

    football_keywords = ['futebol', 'football', 'soccer',
                         'brasileirão', 'champions', 'liga', 'serie a', 'serie b']
    basketball_keywords = ['basquete', 'basketball', 'nba', 'euroleague']
    tennis_keywords = ['tênis', 'tennis',
                       'wimbledon', 'roland garros', 'us open']

    if any(word in text_lower for word in football_keywords):
        return 'football'
    elif any(word in text_lower for word in basketball_keywords):
        return 'basketball'
    elif any(word in text_lower for word in tennis_keywords):
        return 'tennis'
    else:
        return 'football'  # Default


def extract_teams_from_text(text: str) -> str:
    """Extrai nomes dos times do texto"""
    # Palavras que NÃO são nomes de times e devem ser ignoradas
    ignore_words = [
        'previsão', 'previsao', 'terminado', 'finalizado', 'ao vivo', 
        'adiado', 'adiada', 'postponed', 'cancelado', 'cancelada', 
        'cancelled', 'canceled', 'encerrado',
        'live', 'hoje', 'amanhã', 'amanha',
        'preview', 'resultado', 'placar', 'transmissão', 'transmissao'
    ]
    
    # Remove horários (formato HH:MM)
    clean_text = re.sub(r'\d{1,2}:\d{2}', '', text)
    
    # Procura pelo separador "vs" ou "versus" (case insensitive)
    # Tenta diferentes padrões de separadores
    separator_pattern = r'\s+(?:vs\.?|versus)\s+'
    parts = re.split(separator_pattern, clean_text, flags=re.IGNORECASE)
    
    if len(parts) >= 2:
        # Encontrou o separador, extrai os dois times
        team1_text = parts[0].strip()
        team2_text = parts[1].strip()
        
        # Limpa cada time removendo palavras irrelevantes
        def clean_team_name(team_text):
            # Remove quebras de linha e múltiplos espaços
            team_text = ' '.join(team_text.split())
            
            # Remove placares e números no final (ex: "2-1", "3...", "1-", etc)
            team_text = re.sub(r'\s*\d+[\-\.\s:]*\d*[\.\s]*$', '', team_text)
            
            # Remove caracteres especiais mantendo apenas letras, números e hífens
            team_text = re.sub(r'[^\w\s-]', ' ', team_text)
            
            # Divide em palavras
            words = team_text.split()
            
            # Filtra palavras válidas (não números puros)
            valid_words = [
                word for word in words 
                if len(word) > 1 and word.lower() not in ignore_words and not word.isdigit()
            ]
            
            return ' '.join(valid_words).strip()
        
        team1 = clean_team_name(team1_text)
        team2 = clean_team_name(team2_text)
        
        if team1 and team2:
            return f"{team1} vs {team2}"
    
    # Fallback: método antigo se não encontrar "vs"
    # Remove caracteres especiais e números
    clean_text = re.sub(r'[^\w\s-]', ' ', clean_text)
    
    # Filtra palavras válidas (maiores que 2 caracteres e não estão na lista de ignorar)
    words = [
        word for word in clean_text.split() 
        if len(word) > 2 and word.lower() not in ignore_words
    ]

    # Procura por padrões comuns de times
    if len(words) >= 2:
        # Tenta encontrar dois nomes de times
        team1 = words[0]
        team2 = words[1] if len(words) > 1 else "Time 2"
        return f"{team1} vs {team2}"

    return "Times não identificados"


def extract_time_from_text(text: str) -> str:
    """Extrai horário do texto"""
    # Procura por padrões de horário
    time_patterns = [
        r'\d{1,2}:\d{2}',  # HH:MM
        r'\d{1,2}h\d{2}',  # HHhMM
        r'\d{1,2}:\d{2}:\d{2}'  # HH:MM:SS
    ]

    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().replace('h', ':')

    # Se não encontrar, retorna horário atual
    return datetime.now().strftime("%H:%M")


def extract_league_from_text(text: str) -> str:
    """Extrai liga do texto"""
    league_keywords = [
        'brasileirão', 'serie a', 'serie b', 'champions', 'europa league',
        'copa do brasil', 'libertadores', 'sul-americana', 'nba', 'euroleague'
    ]

    text_lower = text.lower()
    for keyword in league_keywords:
        if keyword in text_lower:
            return keyword.title()

    return 'Liga não identificada'

