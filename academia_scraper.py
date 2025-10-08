#!/usr/bin/env python3
"""
Robô para extrair dados da Academia das Apostas Brasil
e cadastrar na API local
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re

@dataclass
class Odds:
    bookmaker: str
    value: float

@dataclass
class Tip:
    id: str
    category: str  # 'football' | 'basketball' | 'tennis'
    league: str
    teams: str
    matchTime: str
    prediction: str
    isPremium: bool
    odds: List[Odds]

class AcademiaScraper:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Configura o driver do Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executa sem interface gráfica
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"Erro ao configurar o driver: {e}")
            print("Certifique-se de que o ChromeDriver está instalado e no PATH")
            raise
    
    def get_main_page_data(self) -> List[Dict]:
        """Extrai dados da página principal"""
        try:
            print("Acessando a página principal...")
            self.driver.get("https://www.academiadasapostasbrasil.com/")
            
            # Aguarda a página carregar
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Aguarda um pouco mais para o JavaScript carregar
            time.sleep(5)
            
            # Procura pela tabela usando diferentes seletores
            table_selectors = [
                ".widget-double-container-left.mb-content .widget-double.livescores.large .tabs_framed.small_tabs .fh_main_tab tbody",
                ".livescores tbody",
                ".widget-double tbody",
                "tbody"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Tabela encontrada com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not table:
                print("Tabela não encontrada. Tentando método alternativo...")
                return self.get_data_alternative_method()
            
            # Extrai as primeiras 5 linhas
            rows = table.find_elements(By.TAG_NAME, "tr")[:5]
            print(f"Encontradas {len(rows)} linhas na tabela")
            
            match_data = []
            for i, row in enumerate(rows):
                try:
                    print(f"Processando linha {i+1}...")
                    match_info = self.extract_row_data(row, i+1)
                    if match_info:
                        match_data.append(match_info)
                except Exception as e:
                    print(f"Erro ao processar linha {i+1}: {e}")
                    continue
            
            return match_data
            
        except Exception as e:
            print(f"Erro ao acessar página principal: {e}")
            return []
    
    def get_data_alternative_method(self) -> List[Dict]:
        """Método alternativo para extrair dados quando a tabela específica não é encontrada"""
        try:
            # Procura por qualquer elemento que contenha dados de partidas
            match_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='match'], [class*='game'], [class*='fixture']")
            
            if not match_elements:
                # Procura por links que possam ser de partidas
                match_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='match'], a[href*='game'], a[href*='fixture']")
            
            print(f"Encontrados {len(match_elements)} elementos de partida")
            
            match_data = []
            for i, element in enumerate(match_elements[:5]):
                try:
                    match_info = self.extract_element_data(element, i+1)
                    if match_info:
                        match_data.append(match_info)
                except Exception as e:
                    print(f"Erro ao processar elemento {i+1}: {e}")
                    continue
            
            return match_data
            
        except Exception as e:
            print(f"Erro no método alternativo: {e}")
            return []
    
    def extract_row_data(self, row, row_number: int) -> Optional[Dict]:
        """Extrai dados de uma linha da tabela"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 3:
                return None
            
            # Procura por link na linha
            link_element = None
            for cell in cells:
                try:
                    link = cell.find_element(By.TAG_NAME, "a")
                    if link and link.get_attribute("href"):
                        link_element = link
                        break
                except NoSuchElementException:
                    continue
            
            if not link_element:
                print(f"Link não encontrado na linha {row_number}")
                return None
            
            link_url = link_element.get_attribute("href")
            print(f"Link encontrado: {link_url}")
            
            # Extrai informações básicas da linha
            row_text = row.text.strip()
            print(f"Texto da linha: {row_text}")
            
            # Cria ID único baseado na URL e timestamp
            match_id = f"match_{hash(link_url)}_{int(time.time())}"
            
            # Tenta determinar categoria baseada no texto
            category = self.determine_category(row_text)
            
            # Extrai times (assumindo formato padrão)
            teams = self.extract_teams_from_text(row_text)
            
            # Extrai horário (se disponível)
            match_time = self.extract_time_from_text(row_text)
            
            # Cria dados básicos
            match_data = {
                'id': match_id,
                'category': category,
                'league': 'Liga não identificada',
                'teams': teams,
                'matchTime': match_time,
                'prediction': 'Predição não disponível',
                'isPremium': False,
                'odds': [],
                'detail_url': link_url
            }
            
            # Tenta acessar a página de detalhes
            try:
                detail_data = self.get_match_details(link_url)
                if detail_data:
                    match_data.update(detail_data)
            except Exception as e:
                print(f"Erro ao acessar detalhes da partida: {e}")
            
            return match_data
            
        except Exception as e:
            print(f"Erro ao extrair dados da linha: {e}")
            return None
    
    def extract_element_data(self, element, element_number: int) -> Optional[Dict]:
        """Extrai dados de um elemento de partida"""
        try:
            link_url = element.get_attribute("href")
            if not link_url:
                return None
            
            element_text = element.text.strip()
            print(f"Elemento {element_number}: {element_text}")
            
            match_id = f"match_{hash(link_url)}_{int(time.time())}"
            category = self.determine_category(element_text)
            teams = self.extract_teams_from_text(element_text)
            match_time = self.extract_time_from_text(element_text)
            
            match_data = {
                'id': match_id,
                'category': category,
                'league': 'Liga não identificada',
                'teams': teams,
                'matchTime': match_time,
                'prediction': 'Predição não disponível',
                'isPremium': False,
                'odds': [],
                'detail_url': link_url
            }
            
            # Tenta acessar detalhes
            try:
                detail_data = self.get_match_details(link_url)
                if detail_data:
                    match_data.update(detail_data)
            except Exception as e:
                print(f"Erro ao acessar detalhes: {e}")
            
            return match_data
            
        except Exception as e:
            print(f"Erro ao extrair dados do elemento: {e}")
            return None
    
    def get_match_details(self, url: str) -> Optional[Dict]:
        """Acessa a página de detalhes da partida"""
        try:
            print(f"Acessando detalhes: {url}")
            
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
            odds_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='odd'], [class*='bet'], [class*='quote']")
            odds = []
            
            for odd_element in odds_elements[:5]:  # Limita a 5 odds
                try:
                    odd_text = odd_element.text.strip()
                    if re.match(r'^\d+\.?\d*$', odd_text):
                        odds.append(Odds(bookmaker="Casa de apostas", value=float(odd_text)))
                except:
                    continue
            
            details['odds'] = [{'bookmaker': o.bookmaker, 'value': o.value} for o in odds]
            
            # Procura por predição
            prediction_selectors = [
                "[class*='prediction']",
                "[class*='tip']",
                "[class*='recommendation']",
                ".prediction",
                ".tip"
            ]
            
            for selector in prediction_selectors:
                try:
                    pred_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    details['prediction'] = pred_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Procura por liga
            league_selectors = [
                "[class*='league']",
                "[class*='competition']",
                "[class*='tournament']",
                ".league"
            ]
            
            for selector in league_selectors:
                try:
                    league_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    details['league'] = league_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Verifica se é premium
            premium_indicators = self.driver.find_elements(By.CSS_SELECTOR, "[class*='premium'], [class*='vip'], [class*='pro']")
            details['isPremium'] = len(premium_indicators) > 0
            
            # Fecha a aba de detalhes
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return details
            
        except Exception as e:
            print(f"Erro ao acessar detalhes da partida: {e}")
            # Tenta voltar para a aba principal
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None
    
    def determine_category(self, text: str) -> str:
        """Determina a categoria do esporte baseada no texto"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['futebol', 'football', 'soccer', 'brasileirão', 'champions']):
            return 'football'
        elif any(word in text_lower for word in ['basquete', 'basketball', 'nba']):
            return 'basketball'
        elif any(word in text_lower for word in ['tênis', 'tennis', 'wimbledon']):
            return 'tennis'
        else:
            return 'football'  # Default
    
    def extract_teams_from_text(self, text: str) -> str:
        """Extrai nomes dos times do texto"""
        # Remove caracteres especiais e números
        clean_text = re.sub(r'[^\w\s-]', ' ', text)
        words = clean_text.split()
        
        # Procura por padrões comuns de times
        if len(words) >= 2:
            # Assume que os primeiros nomes são os times
            return f"{words[0]} vs {words[1]}"
        
        return "Times não identificados"
    
    def extract_time_from_text(self, text: str) -> str:
        """Extrai horário do texto"""
        # Procura por padrões de horário
        time_pattern = r'\d{1,2}:\d{2}'
        match = re.search(time_pattern, text)
        
        if match:
            return match.group()
        
        # Se não encontrar, retorna horário atual
        return datetime.now().strftime("%H:%M")
    
    def send_to_api(self, tip_data: Dict) -> bool:
        """Envia dados para a API local"""
        try:
            api_url = f"{self.api_base_url}/api/tips"
            
            response = requests.post(
                api_url,
                json=tip_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Tip cadastrada com sucesso: {tip_data['id']}")
                return True
            else:
                print(f"❌ Erro ao cadastrar tip: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na requisição para API: {e}")
            return False
    
    def run(self):
        """Executa o processo completo"""
        try:
            print("🚀 Iniciando robô da Academia das Apostas Brasil...")
            
            # Extrai dados da página principal
            match_data = self.get_main_page_data()
            
            if not match_data:
                print("❌ Nenhum dado foi extraído da página")
                return
            
            print(f"📊 Encontrados {len(match_data)} partidas")
            
            # Envia dados para a API
            success_count = 0
            for i, match in enumerate(match_data, 1):
                print(f"\n📤 Enviando partida {i}/{len(match_data)}...")
                
                # Remove URL de detalhes antes de enviar
                match_copy = match.copy()
                match_copy.pop('detail_url', None)
                
                if self.send_to_api(match_copy):
                    success_count += 1
                
                # Pequena pausa entre requisições
                time.sleep(1)
            
            print(f"\n✅ Processo concluído! {success_count}/{len(match_data)} partidas cadastradas com sucesso")
            
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fechado")

def main():
    """Função principal"""
    print("🤖 Robô Academia das Apostas Brasil")
    print("=" * 50)
    
    # Configurações
    api_url = input("Digite a URL da sua API (padrão: http://localhost:8000): ").strip()
    if not api_url:
        api_url = "http://localhost:8000"
    
    # Executa o scraper
    scraper = AcademiaScraper(api_url)
    scraper.run()

if __name__ == "__main__":
    main()
