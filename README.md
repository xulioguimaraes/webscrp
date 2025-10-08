# 🤖 Robô Academia das Apostas Brasil

Este robô automatiza a extração de dados do site da Academia das Apostas Brasil e cadastra as informações na sua API local.

## 📋 Funcionalidades

- ✅ Extrai dados das 5 primeiras partidas da tabela principal
- ✅ Acessa páginas de detalhes para obter informações completas
- ✅ Identifica automaticamente categoria do esporte (futebol, basquete, tênis)
- ✅ Extrai odds, predições, ligas e horários
- ✅ Detecta conteúdo premium
- ✅ Envia dados para sua API local
- ✅ Gerenciamento automático do ChromeDriver

## 🛠️ Instalação

### Pré-requisitos

- Python 3.7 ou superior
- Google Chrome instalado
- Sua API rodando em localhost (ou outra URL)

### Instalação Automática

```bash
# Torna o script executável
chmod +x install_and_run.sh

# Executa a instalação
./install_and_run.sh
```

### Instalação Manual

```bash
# Instala dependências
pip3 install -r requirements.txt

# Instala ChromeDriver automaticamente
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

## 🚀 Como Usar

### Execução Básica

```bash
python3 academia_scraper_improved.py
```

### Configuração da API

Quando executado, o robô solicitará a URL da sua API. Por padrão, usa `http://localhost:8000`.

### Estrutura dos Dados

O robô envia dados no seguinte formato para sua API:

```json
{
  "id": "match_abc123_1703123456",
  "category": "football",
  "league": "Brasileirão",
  "teams": "Flamengo vs Palmeiras",
  "matchTime": "20:00",
  "prediction": "Casa vence",
  "isPremium": false,
  "odds": [
    {
      "bookmaker": "Casa de apostas",
      "value": 2.5
    }
  ]
}
```

## 📁 Arquivos

- `academia_scraper.py` - Versão básica do robô
- `academia_scraper_improved.py` - Versão melhorada (recomendada)
- `requirements.txt` - Dependências Python
- `install_and_run.sh` - Script de instalação automática
- `README.md` - Este arquivo

## 🔧 Configuração da API

Certifique-se de que sua API aceita requisições POST no endpoint `/api/tips` com o formato de dados especificado acima.

### Exemplo de endpoint (Node.js/Express)

```javascript
app.post('/api/tips', (req, res) => {
  const tip = req.body;
  
  // Validação básica
  if (!tip.id || !tip.category || !tip.teams) {
    return res.status(400).json({ error: 'Dados inválidos' });
  }
  
  // Salva no banco de dados
  // ... sua lógica aqui ...
  
  res.status(201).json({ message: 'Tip cadastrada com sucesso', id: tip.id });
});
```

## 🐛 Solução de Problemas

### ChromeDriver não encontrado

```bash
# Instala ChromeDriver manualmente
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())"
```

### Erro de permissão

```bash
# Torna os scripts executáveis
chmod +x install_and_run.sh
chmod +x academia_scraper_improved.py
```

### API não responde

- Verifique se sua API está rodando
- Confirme a URL e porta
- Verifique se o endpoint `/api/tips` existe
- Teste manualmente com curl:

```bash
curl -X POST http://localhost:8000/api/tips \
  -H "Content-Type: application/json" \
  -d '{"id":"test","category":"football","league":"Test","teams":"A vs B","matchTime":"20:00","prediction":"Test","isPremium":false,"odds":[]}'
```

## 📊 Logs e Debug

O robô gera logs detalhados durante a execução:

- ✅ Sucesso
- ⚠️ Avisos
- ❌ Erros
- 📊 Informações de progresso

Para debug, o robô salva um screenshot da página como `debug_page.png`.

## 🔄 Execução Automática

Para executar periodicamente, use cron:

```bash
# Edita crontab
crontab -e

# Adiciona linha para executar a cada hora
0 * * * * cd /caminho/para/o/robô && python3 academia_scraper_improved.py
```

## ⚖️ Considerações Legais

- Respeite os termos de uso do site
- Use com moderação para não sobrecarregar o servidor
- Considere implementar delays entre requisições
- Verifique se o web scraping é permitido

## 🤝 Suporte

Se encontrar problemas:

1. Verifique os logs de erro
2. Confirme se todas as dependências estão instaladas
3. Teste a conectividade com o site
4. Verifique se sua API está funcionando

## 📝 Changelog

### v2.0 (Melhorada)
- Gerenciamento automático do ChromeDriver
- Melhor detecção de elementos
- Logs mais detalhados
- Tratamento de erros aprimorado
- Screenshot para debug

### v1.0 (Básica)
- Funcionalidade básica de scraping
- Envio para API
- Detecção de categoria de esporte
