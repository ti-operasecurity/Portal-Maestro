# 🔐 Maestro - Portal de Aplicações

Portal centralizado de autenticação e acesso às aplicações internas da empresa, com proxy reverso, controle de permissões e segurança em camadas.

**Autor:** [Lucas Franco](https://github.com/LucasDaSilvaFranco) · [LinkedIn](https://www.linkedin.com/in/lucas-franco-tech/)

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Segurança](#segurança)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Deploy](#deploy)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Aplicações Disponíveis](#aplicações-disponíveis)
- [Autenticação e Permissões](#autenticação-e-permissões)
- [Desenvolvimento](#desenvolvimento)
- [Troubleshooting](#troubleshooting)
- [Documentação Adicional](#documentação-adicional)
- [Autor](#-autor)

---

## 🎯 Visão Geral

O **Maestro** é um portal web que centraliza o acesso a múltiplas aplicações internas da empresa, fornecendo:

- ✅ **Autenticação centralizada** com Supabase
- ✅ **Controle de permissões** por usuário e grupo
- ✅ **Proxy reverso** para aplicações internas
- ✅ **Interface responsiva** e moderna
- ✅ **Segurança em camadas** (autenticação + firewall)
- ✅ **HTTPS/SSL** com Let's Encrypt
- ✅ **Rate limiting** e proteção CSRF
- ✅ **Logs de acesso** e auditoria

---

## 🏗️ Arquitetura

### Componentes

```
Internet
   ↓
Firewall Fortinet (portas 80, 443)
   ↓
Nginx Container (proxy reverso + SSL)
   ↓
Rede Docker Interna
   ↓
Flask Container (aplicação principal)
   ↓
Proxy para Aplicações Internas
   ↓
Aplicações (8082, 5253, 8092, etc.)
```

### Fluxo de Acesso

1. **Usuário acessa** `https://maestro.opera.security`
2. **Nginx** recebe a requisição HTTPS (porta 443)
3. **Nginx** faz proxy reverso para Flask (porta 8000 - interna)
4. **Flask** verifica autenticação e permissões
5. **Flask** faz proxy para aplicação interna (se autorizado)
6. **Resposta** retorna ao usuário através do mesmo caminho

### Portas e Serviços

| Porta | Serviço | Exposta? | Acesso |
|-------|---------|----------|--------|
| 80 | HTTP (Nginx) | ✅ Sim | Internet → Redirecionamento HTTPS |
| 443 | HTTPS (Nginx) | ✅ Sim | Internet → Portal Maestro |
| 8000 | Flask | ❌ Não | Apenas Nginx → Flask (rede Docker) |
| 8082, 5253, etc. | Aplicações | ❌ **NÃO** | Apenas Flask → Aplicações (rede interna) |

---

## 🔒 Segurança

### Proteção em Camadas

O Maestro implementa **segurança em camadas**:

#### 1. **Camada de Aplicação (Portal)**
- ✅ Autenticação obrigatória (login)
- ✅ Verificação de permissões por aplicação
- ✅ Controle de acesso baseado em grupos
- ✅ Proteção CSRF
- ✅ Rate limiting
- ✅ Sanitização de inputs
- ✅ Logs de acesso e auditoria

#### 2. **Camada de Rede (Firewall)**
- ✅ **Portas 80 e 443** abertas (acesso ao portal)
- ❌ **Portas das aplicações** devem estar **BLOQUEADAS** no firewall externo
- ✅ Acesso às aplicações apenas através do portal

### ⚠️ Importante: Acesso Direto às Aplicações

**Pergunta:** As aplicações estão acessíveis diretamente pelo IP + porta sem passar pelo portal. Isso é uma falha?

**Resposta:** **NÃO é uma falha do portal**, mas sim uma questão de **configuração do firewall**.

#### Como Funciona

1. **O portal protege o acesso através dele:**
   - Todas as rotas `/proxy/<app_key>` exigem autenticação
   - Verificação de permissões antes de fazer proxy
   - Logs de todos os acessos

2. **As aplicações originais ainda estão rodando:**
   - Exemplo: `http://10.150.16.45:8082/` (Monitoração Produtiva)
   - Se a porta 8082 estiver aberta no firewall externo, ela será acessível diretamente

3. **Solução: Bloquear portas no firewall:**
   - As portas das aplicações (8082, 5253, 8092, etc.) **devem estar bloqueadas** no firewall Fortinet
   - Apenas as portas 80 e 443 (portal) devem estar abertas
   - Isso força todos os acessos a passarem pelo portal

#### Configuração Recomendada no Firewall

```
✅ Permitir:
- Porta 80 (HTTP) → IP do servidor Maestro
- Porta 443 (HTTPS) → IP do servidor Maestro

❌ Bloquear:
- Porta 8082 (Monitoração Produtiva)
- Porta 5253 (Dashboard de Perdas)
- Porta 8092 (Dashboard de Produção)
- Porta 8081 (Monitoramento Fornos)
- Porta 8088 (Robô Logística)
- Porta 8080 (Monitoramento Autoclaves)
- Porta 8079 (Aging de Estoque)
- Porta 4300 (Buffer Forno)
- Porta 5123 (Dash Ocupação Forno)
- Porta 9191 (Dashboard Fluxo por Etapas)
- E todas as outras portas das aplicações
```

#### Verificação

Para verificar se as portas estão bloqueadas:

```bash
# De fora do servidor (de outro computador)
# Deve falhar (timeout ou conexão recusada)
curl http://IP_DO_SERVIDOR:8082
curl http://IP_DO_SERVIDOR:5253
curl http://IP_DO_SERVIDOR:8092

# Apenas estas devem funcionar:
curl http://IP_DO_SERVIDOR      # Porta 80
curl https://IP_DO_SERVIDOR     # Porta 443
```

### Funcionalidades de Segurança

- **Autenticação:** Login com username/password (bcrypt)
- **Sessões:** Cookies seguros (HttpOnly, Secure, SameSite)
- **CSRF Protection:** Tokens CSRF em todos os formulários
- **Rate Limiting:** Limite de tentativas de login e requisições
- **Sanitização:** Limpeza de inputs HTML
- **Validação:** Validação de URLs e dados de entrada
- **Logs:** Registro de acessos, tentativas de login e erros

---

## 📦 Requisitos

### Servidor

- **OS:** Linux (CentOS/RHEL, Ubuntu, Debian)
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Memória:** Mínimo 2GB RAM
- **Disco:** Mínimo 10GB livre
- **Rede:** Acesso à internet (para Let's Encrypt)

### Desenvolvimento Local

- **Python:** 3.11+
- **pip:** 23.0+
- **Node.js:** (opcional, apenas para desenvolvimento frontend)

---

## 🚀 Instalação

### 1. Clonar Repositório

```bash
git clone https://github.com/ti-operasecurity/Portal-Maestro.git
cd Portal-Maestro
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key

# Flask
SECRET_KEY=gerar-chave-secreta-aleatoria-aqui
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# App
DEBUG=False
FLASK_ENV=production
USE_PROXY=True
```

**⚠️ Importante:** Gere uma `SECRET_KEY` segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Instalar Dependências (Desenvolvimento Local)

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### Configuração do Banco de Dados (Supabase)

O Maestro utiliza Supabase como banco de dados. Certifique-se de que as seguintes tabelas existem:

- `maestro_users` - Usuários do sistema
- `maestro_user_groups` - Grupos de usuários
- `maestro_applications` - Aplicações principais
- `maestro_portal_applications` - Aplicações da aba "Aplicações"
- `maestro_user_application_access` - Permissões de acesso
- `maestro_user_portal_app_access` - Permissões de aplicações do portal

Veja os scripts SQL em `sql/` para criar/atualizar o schema.

### Configuração de Aplicações

As aplicações são configuradas em `app.py`:

```python
APLICACOES = [
    {
        'nome': 'Monitoração Produtiva',
        'url': 'http://10.150.16.45:8082/',
        'url_proxy': '/proxy/painel-monitoracao',
        'icone': '📊',
        'cor': '#3b82f6',
        'tamanho': 'pequeno'
    },
    # ... mais aplicações
]

PROXY_ROUTES = {
    'painel-monitoracao': 'http://10.150.16.45:8082',
    # ... mais rotas
}
```

---

## 🚢 Deploy

### Deploy Completo (Produção)

O script `deploy-linux.sh` automatiza todo o processo:

```bash
# Dar permissão de execução
chmod +x deploy-linux.sh

# Deploy completo (construir + iniciar)
./deploy-linux.sh --full-deploy
```

### Opções de Deploy

```bash
# Ver todas as opções
./deploy-linux.sh --help

# Deploy completo (recomendado para primeira vez)
./deploy-linux.sh --full-deploy

# Reiniciar containers (após alterações em código)
./deploy-linux.sh --restart

# Reiniciar rápido (sem rebuild, usando volumes)
./deploy-linux.sh --quick-restart

# Parar containers
./deploy-linux.sh --stop

# Ver status
./deploy-linux.sh --status

# Ver logs
./deploy-linux.sh --logs

# Configurar SSL/HTTPS
./deploy-linux.sh --setup-ssl
```

### Configuração de SSL/HTTPS

1. **Configurar DNS:**
   - Apontar `maestro.opera.security` para o IP do servidor
   - Ver: `docs/CONFIGURAR_DNS_HTTPS.md`

2. **Executar setup SSL:**
   ```bash
   ./deploy-linux.sh --setup-ssl
   ```

3. **Verificar certificado:**
   ```bash
   ./deploy-linux.sh --check-ssl
   ```

### Configuração do Firewall

**Importante:** Configure o firewall Fortinet antes do deploy:

1. **Abrir portas:**
   - Porta 80 (HTTP)
   - Porta 443 (HTTPS)

2. **Bloquear portas das aplicações:**
   - Todas as portas das aplicações (8082, 5253, etc.)

Veja: `docs/CONFIGURAR_FORTINET.md`

---

## 📁 Estrutura do Projeto

```
Maestro/
├── app.py                      # Aplicação Flask principal
├── auth.py                     # Sistema de autenticação
├── security.py                 # Funcionalidades de segurança
├── http_pool.py                # Pool de conexões HTTP
├── monitoring.py                # Monitoramento e métricas
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Imagem Docker
├── docker-compose.yml          # Orquestração Docker
├── deploy-linux.sh             # Script de deploy
├── .env                        # Variáveis de ambiente (não versionado)
│
├── templates/                  # Templates Jinja2
│   ├── index.html             # Página principal
│   ├── login.html             # Página de login
│   ├── applications.html       # Aba de aplicações
│   └── admin/                 # Templates administrativos
│       ├── base.html
│       ├── users.html
│       ├── create_user.html
│       └── edit_user.html
│
├── static/                     # Arquivos estáticos
│   ├── css/
│   │   ├── style.css
│   │   └── login.css
│   ├── js/
│   │   └── login.js
│   └── images/
│       ├── logo_opera.png
│       └── background.png
│
├── config/                     # Configurações
│   ├── nginx/
│   │   ├── nginx.conf         # Configuração HTTPS
│   │   └── nginx-http.conf    # Configuração HTTP (temporária)
│   └── ssl/                    # Certificados SSL
│
├── sql/                        # Scripts SQL para Supabase
│   ├── supabase_add_main_app_*.sql
│   └── supabase_add_portal_app_*.sql
│
├── docs/                       # Documentação
│   ├── DEPLOY_LINUX.md
│   ├── CONFIGURAR_FORTINET.md
│   ├── CONFIGURACAO_PORTAS.md
│   ├── CONFIGURAR_DNS_HTTPS.md
│   └── ...
│
├── logs/                       # Logs da aplicação
│   └── nginx/
│
└── certbot/                    # Certificados Let's Encrypt
    ├── conf/
    └── www/
```

---

## 📱 Aplicações Disponíveis

### Aplicações Principais (Tela Inicial)

- **Monitoração Produtiva** - `http://10.150.16.45:8082/`
- **Dashboard de Perdas** - `http://10.150.16.45:5253/`
- **Dashboard de Produção** - `http://10.150.16.45:8092/`
- **BUFFER do FORNO** - `http://10.150.16.45:4300/buffer`
- **Aging de Estoque** - `http://10.150.16.45:8079/`
- **Dash Ocupação Forno** - `http://10.150.16.45:5123/dashboard_ocupacao`
- **Dashboard de Fluxo por Etapas** - `http://10.150.16.45:9191/`

### Aplicações da Aba "Aplicações"

As aplicações da aba "Aplicações" são gerenciadas dinamicamente através do banco de dados (`maestro_portal_applications`).

---

## 👥 Autenticação e Permissões

### Grupos de Usuários

1. **Administrador**
   - Acesso total ao sistema
   - Pode gerenciar usuários e permissões
   - Acesso a todas as aplicações

2. **Maestro Full**
   - Acesso a todas as aplicações
   - Não pode gerenciar usuários

3. **Operação**
   - Acesso apenas às aplicações permitidas
   - Permissões configuráveis por usuário

### Gerenciamento de Usuários

Acesse `/admin/users` (requer permissão de administrador) para:

- Criar novos usuários
- Editar usuários existentes
- Atribuir grupos
- Conceder/revogar acesso a aplicações
- Ativar/desativar usuários

### Permissões de Aplicações

- **Aplicações Principais:** Gerenciadas através de `maestro_user_application_access`
- **Aplicações do Portal:** Gerenciadas através de `maestro_user_portal_app_access`

---

## 💻 Desenvolvimento

### Executar Localmente (Sem Docker)

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export SUPABASE_URL="..."
export SUPABASE_SERVICE_ROLE_KEY="..."
export SECRET_KEY="..."

# Executar
python app.py
```

Acesse: `http://localhost:5000`

### Atualizações Rápidas (Com Docker)

O `docker-compose.yml` está configurado com volumes para permitir atualizações sem rebuild:

```yaml
volumes:
  - ./app.py:/app/app.py:ro
  - ./auth.py:/app/auth.py:ro
  - ./templates:/app/templates:ro
  - ./static:/app/static:ro
```

Após alterar código:

```bash
# Reiniciar rápido (sem rebuild)
./deploy-linux.sh --quick-restart
```

### Estrutura de Código

- **`app.py`:** Rotas principais, proxy reverso, lógica de aplicações
- **`auth.py`:** Autenticação, permissões, gerenciamento de usuários
- **`security.py`:** CSRF, rate limiting, sanitização, validações
- **`http_pool.py`:** Pool de conexões HTTP para proxy
- **`monitoring.py`:** Métricas de performance e logs

---

## 🔧 Troubleshooting

### Problema: Aplicação não carrega

**Verificações:**
1. Container está rodando? (`./deploy-linux.sh --status`)
2. Logs mostram erros? (`./deploy-linux.sh --logs`)
3. Aplicação interna está acessível? (testar URL diretamente)
4. Permissões do usuário estão corretas?

### Problema: Erro 404 no proxy

**Possíveis causas:**
1. Rota não existe em `PROXY_ROUTES`
2. URL da aplicação interna incorreta
3. Aplicação interna não está rodando

**Solução:**
- Verificar `PROXY_ROUTES` em `app.py`
- Testar URL da aplicação diretamente
- Verificar logs do container

### Problema: Erro de autenticação

**Verificações:**
1. `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estão corretos?
2. Tabelas do banco existem?
3. Usuário está ativo no banco?

### Problema: Acesso direto às aplicações funciona

**Causa:** Portas das aplicações estão abertas no firewall.

**Solução:** Bloquear portas das aplicações no firewall Fortinet. Veja seção [Segurança](#-segurança).

### Problema: SSL não funciona

**Verificações:**
1. DNS está configurado corretamente?
2. Portas 80 e 443 estão abertas?
3. Certificado foi gerado? (`./deploy-linux.sh --check-ssl`)

Veja: `docs/CONFIGURAR_DNS_HTTPS.md`

### Problema: Container demora para subir

**Causa:** `--full-deploy` faz rebuild completo (instala `gcc`, etc.)

**Solução:** Use `--restart` ou `--quick-restart` para alterações de código.

---

## 📚 Documentação Adicional

- **[DEPLOY_LINUX.md](docs/DEPLOY_LINUX.md)** - Guia completo de deploy
- **[CONFIGURAR_FORTINET.md](docs/CONFIGURAR_FORTINET.md)** - Configuração do firewall
- **[CONFIGURACAO_PORTAS.md](docs/CONFIGURACAO_PORTAS.md)** - Detalhes sobre portas
- **[CONFIGURAR_DNS_HTTPS.md](docs/CONFIGURAR_DNS_HTTPS.md)** - Configuração de DNS e SSL
- **[ESTRUTURA_PROJETO.md](docs/ESTRUTURA_PROJETO.md)** - Estrutura detalhada do projeto
- **[GUIA_RAPIDO.md](docs/GUIA_RAPIDO.md)** - Guia rápido de início

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Flask 3.0.0, Python 3.11+
- **Banco de Dados:** Supabase (PostgreSQL)
- **Proxy Reverso:** Nginx
- **Containerização:** Docker, Docker Compose
- **SSL/TLS:** Let's Encrypt (Certbot)
- **Autenticação:** bcrypt, sessions
- **Segurança:** Flask-WTF (CSRF), Flask-Limiter (Rate Limiting), bleach (Sanitização)

---

## 👤 Autor

**Lucas Franco**

- **GitHub:** [https://github.com/LucasDaSilvaFranco](https://github.com/LucasDaSilvaFranco)
- **LinkedIn:** [https://www.linkedin.com/in/lucas-franco-tech/](https://www.linkedin.com/in/lucas-franco-tech/)

Desenvolvedor Full Stack e Especialista em Infraestrutura. Para dúvidas ou contribuições, entre em contato através dos links acima.

---

## 📝 Licença

Este projeto é de uso interno da empresa.

---

## 👤 Suporte

Para problemas ou dúvidas, entre em contato com a equipe de desenvolvimento ou com o [autor](#-autor).

---

**Última atualização:** Fevereiro 2026
