# 🚀 Sequência de Comandos - Deploy no Servidor Linux

## 📋 Passo a Passo Completo

### Passo 1: Transferir Arquivos para o Servidor

**Opção A - Via SCP (do seu computador):**
```bash
scp -r Maestro/ usuario@IP_DO_SERVIDOR:/caminho/destino/
```

**Opção B - Via Git (se usar repositório):**
```bash
# No servidor
git clone SEU_REPOSITORIO
cd Maestro
```

**Opção C - Via FTP/SFTP:**
- Use um cliente FTP (FileZilla, WinSCP, etc.)
- Conecte no servidor
- Faça upload da pasta `Maestro/`

### Passo 2: Conectar no Servidor

```bash
ssh usuario@IP_DO_SERVIDOR
cd /caminho/para/Maestro
```

### Passo 3: Verificar Estrutura

```bash
# Verificar se os arquivos estão presentes
ls -la

# Verificar arquivos essenciais
ls -la docker-compose.yml Dockerfile .env deploy-linux.sh
```

### Passo 4: Configurar Arquivo .env

```bash
# Se o .env não existir, criar a partir do template
cp env_template.txt .env

# Editar o .env com suas configurações
nano .env
# ou
vi .env
```

**Certifique-se de que o .env contém:**
```env
SUPABASE_URL=sua_url_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_aqui
SECRET_KEY=sua_chave_secreta_aqui
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
USE_PROXY=True
```

### Passo 5: Dar Permissão de Execução

```bash
chmod +x deploy-linux.sh
chmod +x scripts/*.sh
```

### Passo 6: Verificar Docker e Docker Compose

```bash
# Verificar se Docker está instalado
docker --version

# Verificar se Docker Compose está instalado
docker-compose --version
# ou
docker compose version

# Se não estiver instalado, instalar:
# CentOS/RHEL:
sudo yum install -y docker docker-compose
# ou
sudo dnf install -y docker docker-compose

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### Passo 7: Executar Deploy Completo

```bash
./deploy-linux.sh --full-deploy
```

Este comando irá:
- ✅ Verificar tudo (Docker, .env, dependências)
- ✅ Verificar estrutura de pastas
- ✅ Construir imagem Docker
- ✅ Iniciar containers (Flask + Nginx)
- ✅ Mostrar instruções sobre Fortinet

### Passo 8: Abrir Portas no Fortinet

**⚠️ IMPORTANTE**: Abra manualmente no painel do Fortinet:

1. **Porta 80 (HTTP)**:
   - Permitir TCP:80 → IP do servidor

2. **Porta 443 (HTTPS)**:
   - Permitir TCP:443 → IP do servidor

3. **NÃO abrir porta 8000** (ela é apenas interna)

Para mais detalhes: `docs/CONFIGURAR_FORTINET.md`

### Passo 9: Verificar Status

```bash
./deploy-linux.sh --status
```

Deve mostrar:
- ✅ Containers rodando (maestro-portal e maestro-nginx)
- ✅ Aplicação respondendo

### Passo 10: Configurar DNS

No painel do seu provedor de DNS:
- Criar registro tipo **A**
- Nome: `maestro`
- Valor: IP do servidor
- TTL: 3600

### Passo 11: Configurar SSL/HTTPS

```bash
./deploy-linux.sh --setup-ssl
```

Este comando irá:
- Verificar DNS
- Obter certificado SSL do Let's Encrypt
- Configurar Nginx com HTTPS

### Passo 12: Verificar Tudo Funcionando

```bash
# Verificar containers
./deploy-linux.sh --status

# Ver logs (se necessário)
./deploy-linux.sh --logs

# Testar acesso
curl -I https://maestro.opera.security
```

### Passo 13: Configurar Renovação Automática do SSL

```bash
# Editar crontab
crontab -e

# Adicionar linha (renova todo dia às 3h)
0 3 * * * /caminho/completo/para/Maestro/scripts/renovar-certificado.sh >> /var/log/maestro-ssl-renew.log 2>&1
```

## 📝 Sequência Resumida (Copy & Paste)

```bash
# 1. Conectar no servidor
ssh usuario@IP_DO_SERVIDOR
cd /caminho/para/Maestro

# 2. Verificar arquivos
ls -la docker-compose.yml .env deploy-linux.sh

# 3. Configurar .env (se necessário)
nano .env

# 4. Dar permissões
chmod +x deploy-linux.sh scripts/*.sh

# 5. Verificar Docker
docker --version
docker-compose --version
sudo systemctl start docker

# 6. Deploy completo
./deploy-linux.sh --full-deploy

# 7. Verificar status
./deploy-linux.sh --status

# 8. Configurar SSL (após DNS)
./deploy-linux.sh --setup-ssl

# 9. Verificar renovação automática
crontab -e
# Adicionar: 0 3 * * * /caminho/para/Maestro/scripts/renovar-certificado.sh
```

## ⚠️ Checklist Pré-Deploy

Antes de executar, verifique:

- [ ] Arquivos transferidos para o servidor
- [ ] Arquivo `.env` configurado com todas as variáveis
- [ ] Docker e Docker Compose instalados
- [ ] Docker rodando (`sudo systemctl start docker`)
- [ ] Permissões de execução dadas aos scripts
- [ ] Portas 80 e 443 abertas no Fortinet (ou abrir após deploy)

## 🔍 Comandos Úteis

### Ver Logs
```bash
./deploy-linux.sh --logs
```

### Parar Containers
```bash
./deploy-linux.sh --stop
```

### Reiniciar Containers
```bash
./deploy-linux.sh --restart
```

### Verificar Portas
```bash
./deploy-linux.sh --check-ports
```

### Verificar Dependências
```bash
./deploy-linux.sh --check-deps
```

### Informações do Sistema
```bash
./deploy-linux.sh --info
```

## ❌ Solução de Problemas

### Erro: Docker não encontrado
```bash
# Instalar Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
```

### Erro: Docker Compose não encontrado
```bash
# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Erro: Arquivo .env não encontrado
```bash
# Criar a partir do template
cp env_template.txt .env
nano .env
```

### Erro: Permissão negada
```bash
# Dar permissões
chmod +x deploy-linux.sh
chmod +x scripts/*.sh
```

### Containers não iniciam
```bash
# Ver logs
./deploy-linux.sh --logs

# Verificar Docker
docker ps -a
docker-compose ps
```

## 📚 Documentação Relacionada

- `docs/DEPLOY_LINUX.md` - Guia completo do script
- `docs/CONFIGURAR_FORTINET.md` - Configuração do Fortinet
- `docs/CONFIGURAR_DNS_HTTPS.md` - Configuração DNS e HTTPS
- `docs/CONFIGURACAO_PORTAS.md` - Explicação sobre portas

## ✅ Checklist Pós-Deploy

- [ ] Containers rodando (`./deploy-linux.sh --status`)
- [ ] Portas 80 e 443 abertas no Fortinet
- [ ] DNS configurado e propagado
- [ ] SSL/HTTPS configurado
- [ ] Aplicação acessível em `https://maestro.opera.security`
- [ ] Renovação automática do SSL configurada
- [ ] Logs verificados (sem erros)

---

**Pronto!** Siga esta sequência e sua aplicação estará funcionando! 🎉

