#!/usr/bin/env python3
"""
Robô melhorado para extrair dados da Academia das Apostas Brasil
e cadastrar na API local
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import uuid


@dataclass
class Odds:
    house: str
    value: float


@dataclass
class Tip:
    id: str
    category: str  # 'football' | 'basketball' | 'tennis'
    league: str
    teams: str
    matchTime: str
    prediction: str
    description: str
    odds: List[Odds]


class AcademiaScraperImproved:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Configura o driver do Selenium com webdriver-manager"""
        print("🔧 Configurando ChromeDriver...")

        chrome_options = Options()
        # Executa sem interface gráfica
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            # Usa webdriver-manager para baixar e gerenciar o ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            print("✅ ChromeDriver configurado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao configurar o driver: {e}")
            print("Certifique-se de que o Google Chrome está instalado")
            raise

    def is_match_finished(self, text: str) -> bool:
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

    def get_main_page_data(self) -> List[Dict]:
        """Extrai dados da página principal"""
        try:
            print("🌐 Acessando a página principal...")
            self.driver.get("https://www.academiadasapostasbrasil.com/")

            # Aguarda a página carregar
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Aguarda um pouco mais para o JavaScript carregar
            time.sleep(5)

            # Salva screenshot para debug (opcional)
            try:
                self.driver.save_screenshot("debug_page.png")
                print("📸 Screenshot salvo como debug_page.png")
            except:
                pass

            # Procura pela tabela usando diferentes seletores
            table_selectors = [
                ".widget-double-container-left.mb-content .widget-double.livescores.large .tabs_framed.small_tabs .fh_main_tab tbody",
                ".livescores tbody",
                ".widget-double tbody",
                ".mb-content tbody",
                "tbody"
            ]

            table = None
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Tabela encontrada com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not table:
                print(
                    "⚠️ Tabela específica não encontrada. Tentando método alternativo...")
                return self.get_data_alternative_method()

            # Busca todas as linhas disponíveis
            all_rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"📊 Encontradas {len(all_rows)} linhas na tabela")

            # Processa linhas até conseguir 5 partidas válidas (não terminadas)
            match_data = []
            max_matches = 5
            
            for i, row in enumerate(all_rows):
                # Para quando já tiver 5 partidas válidas
                if len(match_data) >= max_matches:
                    break
                    
                try:
                    print(f"🔄 Processando linha {i+1}...")
                    match_info = self.extract_row_data(row, i+1)
                    if match_info:
                        match_data.append(match_info)
                        print(f"   ✅ Partida válida adicionada ({len(match_data)}/{max_matches})")
                except Exception as e:
                    print(f"❌ Erro ao processar linha {i+1}: {e}")
                    continue

            return match_data

        except Exception as e:
            print(f"❌ Erro ao acessar página principal: {e}")
            return []

    def get_data_alternative_method(self) -> List[Dict]:
        """Método alternativo para extrair dados quando a tabela específica não é encontrada"""
        try:
            print("🔍 Procurando elementos de partida alternativos...")

            # Procura por diferentes tipos de elementos que podem conter dados de partidas
            selectors_to_try = [
                "[class*='match']",
                "[class*='game']",
                "[class*='fixture']",
                "[class*='event']",
                "a[href*='match']",
                "a[href*='game']",
                "a[href*='fixture']",
                ".match-row",
                ".game-row",
                ".fixture-row"
            ]

            match_elements = []
            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    match_elements.extend(elements)
                    print(
                        f"✅ Encontrados {len(elements)} elementos com seletor: {selector}")

            # Remove duplicatas
            match_elements = list(set(match_elements))
            print(
                f"📊 Total de elementos únicos encontrados: {len(match_elements)}")

            # Processa elementos até conseguir 5 partidas válidas (não terminadas)
            match_data = []
            max_matches = 5
            
            for i, element in enumerate(match_elements):
                # Para quando já tiver 5 partidas válidas
                if len(match_data) >= max_matches:
                    break
                    
                try:
                    print(f"🔄 Processando elemento {i+1}...")
                    match_info = self.extract_element_data(element, i+1)
                    if match_info:
                        match_data.append(match_info)
                        print(f"   ✅ Partida válida adicionada ({len(match_data)}/{max_matches})")
                except Exception as e:
                    print(f"❌ Erro ao processar elemento {i+1}: {e}")
                    continue

            return match_data

        except Exception as e:
            print(f"❌ Erro no método alternativo: {e}")
            return []

    def extract_row_data(self, row, row_number: int) -> Optional[Dict]:
        """Extrai dados de uma linha da tabela"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2:
                print(
                    f"⚠️ Linha {row_number} tem poucas colunas ({len(cells)})")
                return None

            # Extrai informações básicas da linha
            row_text = row.text.strip()
            print(f"📝 Texto da linha: {row_text[:100]}...")
            
            # Verifica se a partida já terminou (ignora jogos terminados)
            if self.is_match_finished(row_text):
                print(f"⏭️  Partida terminada detectada na linha {row_number} - Ignorando...")
                return None

            # Procura por link na linha
            link_element = None
            link_url = None

            for cell in cells:
                try:
                    links = cell.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ("match" in href.lower() or "game" in href.lower() or "fixture" in href.lower()):
                            link_element = link
                            link_url = href
                            break
                    if link_url:
                        break
                except NoSuchElementException:
                    continue

            if not link_url:
                print(f"⚠️ Link não encontrado na linha {row_number}")
                # Tenta usar o texto da linha mesmo sem link
                return self.create_basic_match_data(row_text, row_number)

            print(f"🔗 Link encontrado: {link_url}")

            # Cria dados básicos
            match_data = self.create_basic_match_data(
                row_text, row_number, link_url)

            # Tenta acessar a página de detalhes
            try:
                detail_data = self.get_match_details(link_url)
                if detail_data:
                    match_data.update(detail_data)
            except Exception as e:
                print(f"⚠️ Erro ao acessar detalhes da partida: {e}")

            return match_data

        except Exception as e:
            print(f"❌ Erro ao extrair dados da linha: {e}")
            return None

    def extract_element_data(self, element, element_number: int) -> Optional[Dict]:
        """Extrai dados de um elemento de partida"""
        try:
            link_url = element.get_attribute("href")
            element_text = element.text.strip()

            print(f"📝 Elemento {element_number}: {element_text[:100]}...")

            if not link_url and not element_text:
                return None
            
            # Verifica se a partida já terminou (ignora jogos terminados)
            if self.is_match_finished(element_text):
                print(f"⏭️  Partida terminada detectada no elemento {element_number} - Ignorando...")
                return None

            match_data = self.create_basic_match_data(
                element_text, element_number, link_url)

            # Tenta acessar detalhes se houver link
            if link_url:
                try:
                    detail_data = self.get_match_details(link_url)
                    if detail_data:
                        match_data.update(detail_data)
                except Exception as e:
                    print(f"⚠️ Erro ao acessar detalhes: {e}")

            return match_data

        except Exception as e:
            print(f"❌ Erro ao extrair dados do elemento: {e}")
            return None

    def create_basic_match_data(self, text: str, number: int, link_url: str = None) -> Dict:
        """Cria dados básicos de uma partida"""
        # Gera ID único
        match_id = f"match_{uuid.uuid4().hex[:8]}_{int(time.time())}"

        # Determina categoria
        category = self.determine_category(text)

        # Extrai times
        teams = self.extract_teams_from_text(text)

        # Extrai horário e adiciona data atual
        match_time = self.extract_time_from_text(text)
        current_date = datetime.now().strftime("%Y-%m-%d")
        match_time = f"{current_date} {match_time}"

        # Extrai liga
        league = self.extract_league_from_text(text)

        return {
            'id': match_id,
            'category': category,
            'league': league,
            'teams': teams,
            'matchTime': match_time,
            'prediction': 'Predição não disponível',
            'description': '',
            'odds': [],
            'detail_url': link_url
        }

    def get_match_details(self, url: str) -> Optional[Dict]:
        """Acessa a página de detalhes da partida"""
        try:
            print(f"🔍 Acessando detalhes: {url}")

            # Abre nova aba
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])

            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(3)  # Aguarda carregamento

            # Extrai informações da página de detalhes
            details = {}

            # Procura por odds
            odds = self.extract_odds_from_page()
            details['odds'] = [asdict(odd) for odd in odds]

            # Procura por predição
            prediction = self.extract_prediction_from_page()
            if prediction:
                details['prediction'] = prediction

            # Procura por description (nova propriedade)
            description = self.extract_description_from_page()
            if description:
                details['description'] = description

            # Procura por liga
            league = self.extract_league_from_page()
            if league:
                details['league'] = league

            # Verifica se é premium (DESABILITADO)
            # details['isPremium'] = self.check_if_premium()

            # Fecha a aba de detalhes
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return details

        except Exception as e:
            print(f"❌ Erro ao acessar detalhes da partida: {e}")
            # Tenta voltar para a aba principal
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    def extract_odds_from_page(self) -> List[Odds]:
        """Extrai odds da página de detalhes"""
        odds = []

        # Seletores ESPECÍFICOS para odds
        odds_selectors = [
            # Seletor específico fornecido
            "bet-suggestion > preview_bet_odd > div.preview_bet > p.preview_odd",
            ".bet-suggestion .preview_bet_odd .preview_bet p.preview_odd",
            ".preview_bet p.preview_odd",
            "p.preview_odd",
            
            # Seletores genéricos como fallback
            "[class*='odd']",
            "[class*='bet']",
            "[class*='quote']",
            "[class*='price']",
            ".odds",
            ".bet-odds"
        ]

        for selector in odds_selectors:
            try:
                odds_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🎲 Testando seletor de odds '{selector}': {len(odds_elements)} elementos")
                
                # Pega apenas o PRIMEIRO elemento (apenas 1 odd)
                if odds_elements:
                    element = odds_elements[0]
                    try:
                        odd_text = element.text.strip()
                        
                        # Extrai números do texto (ex: "Odd 1.95" -> "1.95")
                        match = re.search(r'\d+\.?\d*', odd_text)
                        if match:
                            odd_value = float(match.group())
                            odds.append(Odds(house="Bet365", value=odd_value))
                            print(f"   ✅ Odd encontrada: {odd_value} (texto original: '{odd_text}')")
                    except:
                        pass
                        
                if odds:
                    print(f"✅ Odd cadastrada com seletor '{selector}'")
                    break
            except Exception as e:
                continue

        if not odds:
            print("⚠️ Nenhuma odd encontrada")
            
        return odds

    def extract_description_from_page(self) -> Optional[str]:
        """Extrai description da página de detalhes (Sugestão de aposta + Previsão)"""
        descriptions = []
        
        # PRIMEIRA INFORMAÇÃO: Sugestão de aposta
        suggestion_selectors = [
            "#_preview div.preview_main_container article div.preview_resume div.preview_intro.toggle_content",
            "div.preview_resume div.preview_intro.toggle_content",
            "div.preview_intro.toggle_content",
            ".preview_intro.toggle_content"
        ]
        
        suggestion_text = None
        for selector in suggestion_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"📝 Testando seletor de sugestão '{selector}': {len(elements)} elementos")
                if elements:
                    suggestion_text = elements[0].text.strip()
                    if suggestion_text and len(suggestion_text) > 3:
                        print(f"✅ Sugestão de aposta encontrada: {suggestion_text[:50]}...")
                        break
            except Exception as e:
                continue
        
        if suggestion_text:
            descriptions.append(f"**Sugestão de aposta:**\n{suggestion_text}")
        
        # SEGUNDA INFORMAÇÃO: Previsão
        preview_selectors = [
            "#_preview div.preview_main_container article div.preview_pre_intro div.preview_body",
            "div.preview_pre_intro div.preview_body",
            "div.preview_body"
        ]
        
        preview_text = None
        for selector in preview_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"📝 Testando seletor de previsão '{selector}': {len(elements)} elementos")
                if elements:
                    preview_text = elements[0].text.strip()
                    if preview_text and len(preview_text) > 3:
                        print(f"✅ Previsão encontrada: {preview_text[:50]}...")
                        break
            except Exception as e:
                continue
        
        if preview_text:
            descriptions.append(f"**Previsão:**\n{preview_text}")
        
        # Concatena as duas informações
        if descriptions:
            final_description = "\n\n".join(descriptions)
            print(f"✅ Description completa extraída com sucesso ({len(final_description)} caracteres)")
            return final_description
        
        print("⚠️ Nenhuma description encontrada")
        return ""

    def extract_prediction_from_page(self) -> Optional[str]:
        """Extrai predição da página de detalhes"""
        predictions = []
        
        # PRIMEIRA INFORMAÇÃO: Sugestão de aposta
        suggestion_selectors = [
            "#_preview div.preview_main_container article div.preview_resume div.preview_intro.toggle_content",
            "div.preview_resume div.preview_intro.toggle_content",
            "div.preview_intro.toggle_content",
            ".preview_intro.toggle_content"
        ]
        
        suggestion_text = None
        for selector in suggestion_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔮 Testando seletor de sugestão '{selector}': {len(elements)} elementos")
                if elements:
                    suggestion_text = elements[0].text.strip()
                    if suggestion_text and len(suggestion_text) > 3:
                        print(f"✅ Sugestão de aposta encontrada: {suggestion_text[:50]}...")
                        break
            except Exception as e:
                continue
        
        if suggestion_text:
            predictions.append(f"**Sugestão de aposta:**\n{suggestion_text}")
        
        # SEGUNDA INFORMAÇÃO: Previsão
        preview_selectors = [
            "#_preview div.preview_main_container article div.preview_pre_intro div.preview_body",
            "div.preview_pre_intro div.preview_body",
            "div.preview_body"
        ]
        
        preview_text = None
        for selector in preview_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔮 Testando seletor de previsão '{selector}': {len(elements)} elementos")
                if elements:
                    preview_text = elements[0].text.strip()
                    if preview_text and len(preview_text) > 3:
                        print(f"✅ Previsão encontrada: {preview_text[:50]}...")
                        break
            except Exception as e:
                continue
        
        if preview_text:
            predictions.append(f"**Previsão:**\n{preview_text}")
        
        # Concatena as duas informações
        if predictions:
            final_prediction = "\n\n".join(predictions)
            print(f"✅ Predição completa extraída com sucesso ({len(final_prediction)} caracteres)")
            return final_prediction
        
        # FALLBACK: Seletores antigos caso os novos não funcionem
        print("⚠️ Tentando seletores de fallback...")
        prediction_selectors = [
            "bet-suggestion > preview_bet_odd > div.preview_bet > p",
            ".bet-suggestion .preview_bet_odd .preview_bet > p",
            ".preview_bet > p",
            "div.preview_bet p",
            "[class*='prediction']",
            "[class*='tip']",
            "[class*='recommendation']",
            "[class*='forecast']",
            ".prediction",
            ".tip",
            ".recommendation"
        ]

        for selector in prediction_selectors:
            try:
                pred_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"🔮 Testando seletor de fallback '{selector}': {len(pred_elements)} elementos")
                
                for pred_element in pred_elements:
                    prediction = pred_element.text.strip()
                    if prediction and len(prediction) > 3 and not re.match(r'^\d+\.?\d*$', prediction):
                        print(f"✅ Predição encontrada com fallback '{selector}': {prediction[:50]}...")
                        return prediction
                        
            except NoSuchElementException:
                continue

        print("⚠️ Nenhuma predição encontrada")
        return None

    def extract_league_from_page(self) -> Optional[str]:
        try:
            print("🔍 Procurando por li.gamehead...")
            gamehead_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "td.stats-game-head-date ul li.gamehead")

            if len(gamehead_elements) > 1:
                # Pula o primeiro e tenta os seguintes
                for element in gamehead_elements[2:]:  # [1:] pula o primeiro
                    league = element.text.strip()
                    if league and len(league) > 3:
                        print(
                            f"✅ Liga encontrada pulando o primeiro li.gamehead: {league}")
                        return league
            elif len(gamehead_elements) == 1:
                print(f"⚠️ Apenas 1 li.gamehead encontrado")
            else:
                print(f"⚠️ Nenhum li.gamehead encontrado")
        except Exception as e:
            print(f"⚠️ Erro ao buscar li.gamehead: {e}")

        # ESTRATÉGIA 2: Seletores alternativos
        league_selectors = [
            ".stats-game-head-date ul li.gamehead",
            "ul li.gamehead",
            "[class*='league']",
            "[class*='competition']",
            "[class*='tournament']",
            "[class*='championship']",
            ".league",
            ".competition"
        ]

        for selector in league_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 1:
                    # Pula o primeiro
                    league = elements[1].text.strip()
                    if league and len(league) > 3:
                        print(
                            f"✅ Liga encontrada com seletor '{selector}' (2º elemento): {league}")
                        return league
            except:
                continue

        print("⚠️ Nenhum seletor de liga funcionou")
        return None

    def check_if_premium(self) -> bool:
        """Verifica se o conteúdo é premium"""
        premium_indicators = [
            "[class*='premium']",
            "[class*='vip']",
            "[class*='pro']",
            "[class*='paid']",
            ".premium",
            ".vip"
        ]

        for selector in premium_indicators:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return True
            except:
                continue

        return False

    def determine_category(self, text: str) -> str:
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

    def extract_teams_from_text(self, text: str) -> str:
        """Extrai nomes dos times do texto"""
        # Palavras que NÃO são nomes de times e devem ser ignoradas
        ignore_words = [
            'previsão', 'previsao', 'terminado', 'finalizado', 'ao vivo', 
            'adiado', 'adiada', 'postponed', 'cancelado', 'cancelada', 
            'cancelled', 'canceled', 'encerrado',
            'live', 'vs', 'versus', 'hoje', 'amanhã', 'amanha',
            'preview', 'resultado', 'placar', 'transmissão', 'transmissao'
        ]
        
        # Remove caracteres especiais e números
        clean_text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Remove horários (formato HH:MM)
        clean_text = re.sub(r'\d{1,2}:\d{2}', '', clean_text)
        
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

    def extract_time_from_text(self, text: str) -> str:
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

    def extract_league_from_text(self, text: str) -> str:
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

    def send_to_api(self, tip_data: Dict) -> bool:
        """Envia dados para a API local"""
        try:
            api_url = f"http://localhost:3000/api/tips"

            # Remove campos que não devem ser enviados
            clean_data = {k: v for k, v in tip_data.items() if k !=
                          'detail_url'}

            response = requests.post(
                api_url,
                json=clean_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"✅ Tip cadastrada com sucesso: {tip_data['id']}")
                return True
            else:
                print(
                    f"❌ Erro ao cadastrar tip: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erro na requisição para API: {e}")
            return False

    def run(self):
        """Executa o processo completo"""
        try:
            print("🚀 Iniciando robô da Academia das Apostas Brasil...")
            print("=" * 60)

            # Extrai dados da página principal
            match_data = self.get_main_page_data()

            if not match_data:
                print("❌ Nenhum dado foi extraído da página")
                return

            print(f"📊 Encontrados {len(match_data)} partidas")
            print("=" * 60)

            # Envia dados para a API
            success_count = 0
            for i, match in enumerate(match_data, 1):
                print(f"\n📤 Enviando partida {i}/{len(match_data)}...")
                print(f"   ID: {match['id']}")
                print(f"   Times: {match['teams']}")
                print(f"   Categoria: {match['category']}")

                if self.send_to_api(match):
                    success_count += 1

                # Pequena pausa entre requisições
                time.sleep(1)

            print("\n" + "=" * 60)
            print(
                f"✅ Processo concluído! {success_count}/{len(match_data)} partidas cadastradas com sucesso")

        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fechado")


def main():
    """Função principal"""
    print("🤖 Robô Academia das Apostas Brasil - Versão Melhorada")
    print("=" * 60)

    # Configurações
    api_url = input(
        "Digite a URL da sua API (padrão: http://localhost:8000): ").strip()
    if not api_url:
        api_url = "http://localhost:8000"

    print(f"🌐 API configurada para: {api_url}")
    print("")

    # Executa o scraper
    scraper = AcademiaScraperImproved(api_url)
    scraper.run()


if __name__ == "__main__":
    main()
