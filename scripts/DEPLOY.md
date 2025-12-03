# Guia de Deploy - Portal Maestro

## Pré-requisitos no Servidor

1. Docker instalado e rodando
2. Docker Compose instalado (opcional, mas recomendado)
3. Arquivo `.env` configurado na raiz do projeto
4. Acesso ao servidor via SSH

## Passo a Passo de Deploy

### 1. Transferir Arquivos para o Servidor

```bash
# No seu computador local, compacte os arquivos necessários
tar -czf maestro-deploy.tar.gz \
  app.py \
  auth.py \
  requirements.txt \
  Dockerfile \
  docker-compose.yml \
  .dockerignore \
  deploy-linux.sh \
  templates/ \
  static/ \
  logo_opera.png

# Transfira para o servidor (ajuste o caminho)
scp maestro-deploy.tar.gz usuario@servidor:/caminho/destino/
```

### 2. No Servidor Linux

```bash
# 1. Extrair arquivos
cd /caminho/destino/
tar -xzf maestro-deploy.tar.gz

# 2. Criar arquivo .env (se ainda não existir)
nano .env
# Preencha com:
# SUPABASE_URL=https://seu-projeto.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=sua_chave
# SECRET_KEY=sua_chave_secreta
# SESSION_COOKIE_SECURE=True
# SESSION_COOKIE_HTTPONLY=True
# SESSION_COOKIE_SAMESITE=Lax
# HOST_PORT=8000
# DEBUG=False
```

## Métodos de Deploy

### Método 1: Docker Compose (Recomendado - Mais Simples)

```bash
# 1. Construir e iniciar em um comando
docker-compose up -d --build

# 2. Ver logs
docker-compose logs -f

# 3. Parar
docker-compose down

# 4. Reiniciar
docker-compose restart

# 5. Ver status
docker-compose ps
```

### Método 2: Script de Deploy (Mais Controle)

```bash
# 1. Dar permissão de execução ao script
chmod +x deploy-linux.sh

# 2. Executar deploy completo
./deploy-linux.sh --full-deploy
```

## Comandos Disponíveis

### Docker Compose

```bash
# Construir e iniciar
docker-compose up -d --build

# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs
docker-compose logs -f

# Ver logs das últimas 100 linhas
docker-compose logs --tail=100

# Ver status
docker-compose ps

# Reconstruir sem cache
docker-compose build --no-cache
```

### Script de Deploy

```bash
# Deploy completo (recomendado para primeira vez)
./deploy-linux.sh --full-deploy

# Apenas construir imagem
./deploy-linux.sh --build

# Apenas iniciar container
./deploy-linux.sh --start

# Parar container
./deploy-linux.sh --stop

# Reiniciar container
./deploy-linux.sh --restart

# Ver status
./deploy-linux.sh --status

# Ver logs
./deploy-linux.sh --logs

# Informações do sistema
./deploy-linux.sh --info
```

## Verificação Pós-Deploy

1. Verificar se container está rodando:
   ```bash
   docker ps | grep maestro-portal
   ```

2. Verificar logs:
   ```bash
   ./deploy-linux.sh --logs
   ```

3. Testar aplicação:
   ```bash
   curl http://localhost:8000/login
   ```

4. Acessar no navegador:
   - Local: `http://localhost:8000`
   - Rede: `http://IP_DO_SERVIDOR:8000`

## Troubleshooting

### Container não inicia
- Verifique se o arquivo `.env` existe e está correto
- Verifique logs: `./deploy-linux.sh --logs`
- Verifique se a porta 8000 está disponível

### Erro de autenticação
- Verifique se `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estão corretos
- Verifique se a tabela `maestro_users` existe no Supabase

### Erro ao construir imagem
- Verifique conexão com internet (para baixar dependências)
- Verifique se `requirements.txt` está correto

## Estrutura de Arquivos Necessários

```
Maestro/
├── app.py
├── auth.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── deploy-linux.sh
├── .env (criar no servidor)
├── templates/
│   ├── index.html
│   └── login.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── login.css
│   └── images/
│       └── logo_opera.png
└── logo_opera.png
```

## Variáveis de Ambiente (.env)

```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role

# Flask
SECRET_KEY=sua_chave_secreta_aleatoria
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Docker Compose (opcional)
HOST_PORT=8000
DEBUG=False
FLASK_ENV=production
```

## Segurança

⚠️ **IMPORTANTE:**
- Nunca commite o arquivo `.env` no Git
- Use `SECRET_KEY` forte e aleatória
- Em produção, use HTTPS (configure proxy reverso se necessário)
- Mantenha `SESSION_COOKIE_SECURE=True` apenas com HTTPS

