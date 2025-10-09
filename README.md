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
- ⏰ **Agendamento automático** - Executa todos os dias às 00:01
- 🐳 **100% em Docker** - Funciona em qualquer máquina
- 🔄 **Auto-reinício** - Reinicia sozinho se falhar

## 🛠️ Instalação

### Opção 1: Docker com Agendamento Automático (Recomendado) 🐳⏰

**Não requer Python ou Chrome instalados na sua máquina!**  
**Executa automaticamente todos os dias às 00:01!**

#### Pré-requisitos
- Docker instalado ([Instalar Docker](https://docs.docker.com/get-docker/))
- Sua API configurada no docker-compose.yml (já está!)

#### Método A: Agendamento Automático (Super Fácil!)

```bash
# 1. Construir e iniciar com agendamento automático
docker-compose up -d --build

# Pronto! Agora roda sozinho todos os dias às 00:01 🎉
```

**O que acontece:**
- ✅ Container inicia e fica rodando 24/7
- ✅ Executa imediatamente na primeira vez
- ✅ Depois executa todos os dias às 00:01
- ✅ Se parar ou falhar, reinicia sozinho
- ✅ Logs são salvos automaticamente

**Ver logs:**
```bash
# Logs em tempo real
docker-compose logs -f scraper

# Histórico de execuções
docker exec academia-scraper cat /app/logs/cron.log
```

**Comandos úteis:**
```bash
# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Executar manualmente agora
docker exec academia-scraper python /app/academia_scraper_improved.py
```

**📖 Guia completo**: Veja `AGENDAMENTO_AUTOMATICO.md` para configurar horários, múltiplas execuções, etc.

#### Método B: Usando Docker diretamente

```bash
# 1. Construir a imagem
docker build -t academia-scraper .

# 2. Executar o container (roda uma vez e para)
docker run --rm academia-scraper

# 3. Executar com URL da API customizada
docker run --rm -e API_URL=https://sua-api.com academia-scraper

# 4. Executar salvando screenshots na máquina host
docker run --rm -v $(pwd):/app/output academia-scraper

# 5. Executar com API no localhost da máquina host
docker run --rm --add-host=host.docker.internal:host-gateway \
  -e API_URL=http://host.docker.internal:3000 \
  academia-scraper
```

**Dica**: Use `docker-compose build` para criar a imagem e depois use `docker run` quando quiser executar.

#### Variáveis de Ambiente Docker

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `API_URL` | URL da sua API | `http://localhost:3000` |
| `CHROME_BIN` | Caminho do Chrome | `/usr/bin/chromium` |
| `CHROMEDRIVER_PATH` | Caminho do ChromeDriver | `/usr/bin/chromedriver` |

---

### Opção 2: Instalação Local

#### Pré-requisitos
- Python 3.7 ou superior
- Google Chrome instalado
- Sua API rodando em localhost (ou outra URL)

#### Instalação Automática

```bash
# Torna o script executável
chmod +x install_and_run.sh

# Executa a instalação
./install_and_run.sh
```

#### Instalação Manual

```bash
# Instala dependências
pip3 install -r requirements.txt

# Instala ChromeDriver automaticamente
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

## 🚀 Como Usar

### Com Docker

```bash
# Usando docker-compose (mais simples)
docker-compose up

# Ou com docker run
docker run --rm -e API_URL=http://host.docker.internal:3000 academia-scraper
```

### Localmente

```bash
# Execução básica
python3 academia_scraper_improved.py

# Com variável de ambiente
export API_URL=http://localhost:3000
python3 academia_scraper_improved.py
```

### Configuração da API

- **Docker**: Configure a variável `API_URL` no `docker-compose.yml` ou use `-e API_URL=...` no `docker run`
- **Local**: O robô perguntará a URL interativamente, ou defina a variável de ambiente `API_URL`
- **Padrão**: `http://localhost:3000`

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

### Docker

#### Container não inicia
```bash
# Ver logs detalhados
docker-compose logs scraper

# Ou com docker run
docker logs academia-scraper
```

#### Não consegue acessar API no localhost
```bash
# Use host.docker.internal em vez de localhost
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e API_URL=http://host.docker.internal:3000 \
  academia-scraper
```

#### Permissão negada para salvar screenshot
```bash
# Monte um volume com permissões corretas
docker run --rm -v $(pwd)/output:/app/output academia-scraper
```

### Instalação Local

#### ChromeDriver não encontrado
```bash
# Instala ChromeDriver manualmente
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())"
```

#### Erro de permissão
```bash
# Torna os scripts executáveis
chmod +x install_and_run.sh
chmod +x academia_scraper_improved.py
```

### Problemas com a API

- Verifique se sua API está rodando
- Confirme a URL e porta
- Verifique se o endpoint `/api/tips` existe
- Teste manualmente com curl:

```bash
curl -X POST http://localhost:3000/api/tips \
  -H "Content-Type: application/json" \
  -d '{"id":"test","category":"football","league":"Test","teams":"A vs B","matchTime":"2024-01-01 20:00","prediction":"Test","description":"","odds":[]}'
```

## 📊 Logs e Debug

O robô gera logs detalhados durante a execução:

- ✅ Sucesso
- ⚠️ Avisos
- ❌ Erros
- 📊 Informações de progresso

Para debug, o robô salva um screenshot da página como `debug_page.png`.

## 🔄 Execução Automática

### Com Docker

```bash
# Método 1: Usar cron no host para rodar o container
crontab -e

# Adiciona linha para executar a cada hora
0 * * * * docker run --rm -e API_URL=http://host.docker.internal:3000 academia-scraper

# Método 2: Usar docker-compose com restart policy
# O container reinicia automaticamente se falhar
docker-compose up -d
```

### Local (sem Docker)

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
