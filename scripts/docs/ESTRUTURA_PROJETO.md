# Estrutura do Projeto Maestro

Este documento descreve a organização da estrutura de pastas do projeto Maestro Portal.

## 📁 Estrutura de Diretórios

```
Maestro/
├── app/                    # Código da aplicação Flask
│   ├── app.py             # Aplicação principal
│   ├── auth.py            # Sistema de autenticação
│   ├── security.py        # Módulo de segurança
│   ├── http_pool.py       # Pool de conexões HTTP
│   ├── monitoring.py      # Monitoramento de performance
│   ├── templates/         # Templates HTML
│   │   ├── index.html
│   │   └── login.html
│   ├── static/            # Arquivos estáticos
│   │   ├── css/
│   │   └── images/
│   └── logo_opera.png
│
├── config/                # Configurações
│   ├── nginx/            # Configurações do Nginx
│   │   ├── nginx.conf           # Configuração HTTPS
│   │   └── nginx-http.conf      # Configuração HTTP temporária
│   └── ssl/              # Certificados SSL (não versionado)
│
├── scripts/               # Scripts de deploy e manutenção
│   ├── configurar-ssl.sh        # Configurar SSL/HTTPS
│   ├── renovar-certificado.sh   # Renovar certificado SSL
│   ├── organizar-estrutura.sh   # Reorganizar estrutura
│   ├── deploy-compose.sh
│   ├── deploy-linux.sh
│   └── *.sh              # Outros scripts
│
├── docs/                  # Documentação
│   ├── CONFIGURAR_DNS_HTTPS.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── README.md
│   └── *.md              # Outros documentos
│
├── logs/                  # Logs da aplicação
│   └── nginx/            # Logs do Nginx
│
├── certbot/              # Certificados Let's Encrypt (não versionado)
│   ├── conf/
│   └── www/
│
├── docker-compose.yml    # Configuração Docker Compose
├── Dockerfile            # Imagem Docker da aplicação
├── requirements.txt     # Dependências Python
└── .env                 # Variáveis de ambiente (não versionado)
```

## 📦 Descrição das Pastas

### `app/`
Contém todo o código-fonte da aplicação Flask:
- **app.py**: Aplicação principal com rotas e lógica de negócio
- **auth.py**: Sistema de autenticação com Supabase
- **security.py**: Módulos de segurança (CSRF, rate limiting, validação)
- **http_pool.py**: Pool de conexões HTTP para otimização
- **monitoring.py**: Monitoramento de performance e métricas
- **templates/**: Templates Jinja2 para renderização HTML
- **static/**: Arquivos estáticos (CSS, imagens, JS)

### `config/`
Configurações de infraestrutura:
- **nginx/**: Configurações do servidor web Nginx
  - `nginx.conf`: Configuração principal com HTTPS
  - `nginx-http.conf`: Configuração temporária para obter certificado
- **ssl/**: Certificados SSL (não versionado no git)

### `scripts/`
Scripts utilitários para deploy e manutenção:
- **configurar-ssl.sh**: Configura SSL/HTTPS com Let's Encrypt
- **renovar-certificado.sh**: Renova certificado SSL automaticamente
- **organizar-estrutura.sh**: Reorganiza estrutura de pastas
- Outros scripts de deploy e gerenciamento

### `docs/`
Documentação do projeto:
- Guias de configuração
- Documentação técnica
- README e outros documentos

### `logs/`
Logs da aplicação:
- Logs do Nginx
- Logs da aplicação Flask (se configurado)

### `certbot/`
Certificados SSL do Let's Encrypt (não versionado):
- **conf/**: Configurações e certificados
- **www/**: Diretório webroot para validação

## 🔒 Arquivos Não Versionados

Os seguintes arquivos/pastas NÃO devem ser versionados no Git:
- `.env` - Variáveis de ambiente sensíveis
- `config/ssl/` - Certificados SSL
- `certbot/` - Certificados Let's Encrypt
- `logs/` - Logs da aplicação
- `__pycache__/` - Cache Python

Adicione ao `.gitignore`:
```
.env
config/ssl/
certbot/
logs/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
```

## 🚀 Fluxo de Deploy

1. **Desenvolvimento**: Código em `app/`
2. **Build**: Docker constrói imagem a partir de `Dockerfile`
3. **Deploy**: Docker Compose orquestra containers
4. **Proxy**: Nginx faz proxy reverso para aplicação Flask
5. **SSL**: Certificados gerenciados pelo Certbot

## 📝 Manutenção

### Adicionar Nova Aplicação
1. Editar `app/app.py` - adicionar à lista `APLICACOES`
2. Adicionar rota em `PROXY_ROUTES`
3. Rebuild e redeploy

### Atualizar Configuração Nginx
1. Editar `config/nginx/nginx.conf`
2. Reiniciar container: `docker-compose restart nginx`

### Atualizar Dependências
1. Editar `requirements.txt`
2. Rebuild: `docker-compose build`
3. Redeploy: `docker-compose up -d`

