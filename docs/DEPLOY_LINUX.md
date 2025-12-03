# 🚀 Guia de Deploy - deploy-linux.sh

## Visão Geral

O script `deploy-linux.sh` foi atualizado para suportar **deploy completo** com:
- ✅ Flask (aplicação)
- ✅ Nginx (proxy reverso)
- ✅ HTTPS/SSL (Let's Encrypt)
- ✅ Verificação automática de firewall

## 🎯 Uso Rápido

### Deploy Completo (Recomendado)

```bash
chmod +x deploy-linux.sh
./deploy-linux.sh --full-deploy
```

Este comando irá:
1. ✅ Verificar Docker e Docker Compose
2. ✅ Verificar estrutura do projeto
3. ✅ Verificar arquivo .env
4. ✅ Verificar dependências de segurança
5. ✅ Verificar e configurar firewall (portas 80 e 443)
6. ✅ Construir imagem Docker
7. ✅ Iniciar containers (Flask + Nginx)
8. ✅ Deixar tudo pronto para uso

### Após o Deploy

1. **Abrir portas no firewall** (se ainda não estiverem abertas):
   ```bash
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

2. **Configurar DNS** (apontar `maestro.opera.security` para o IP do servidor)

3. **Configurar SSL/HTTPS**:
   ```bash
   ./deploy-linux.sh --setup-ssl
   ```

## 📋 Comandos Disponíveis

### Comandos Principais

```bash
# Deploy completo (tudo de uma vez)
./deploy-linux.sh --full-deploy

# Configurar SSL/HTTPS (após deploy)
./deploy-linux.sh --setup-ssl

# Iniciar containers
./deploy-linux.sh --start

# Parar containers
./deploy-linux.sh --stop

# Reiniciar containers
./deploy-linux.sh --restart

# Ver status
./deploy-linux.sh --status

# Ver logs
./deploy-linux.sh --logs
```

### Comandos de Verificação

```bash
# Verificar portas do firewall
./deploy-linux.sh --check-ports

# Verificar dependências
./deploy-linux.sh --check-deps

# Informações do sistema
./deploy-linux.sh --info
```

## 🔧 O Que o Script Faz

### 1. Verificações Automáticas

- ✅ Docker e Docker Compose instalados
- ✅ Estrutura de pastas correta
- ✅ Arquivo .env configurado
- ✅ Dependências de segurança presentes
- ✅ Portas 80 e 443 disponíveis
- ✅ Firewall configurado (oferece configurar automaticamente)

### 2. Configuração do Firewall

O script verifica e oferece configurar automaticamente:
- ✅ Abre portas 80 (HTTP) e 443 (HTTPS)
- ✅ Remove porta 8000 se estiver exposta (não deve estar)

### 3. Deploy

- ✅ Para containers existentes
- ✅ Constrói imagem Docker
- ✅ Inicia containers com Docker Compose
- ✅ Configura Nginx como proxy reverso
- ✅ Deixa tudo pronto para uso

## 📝 Fluxo Completo

### Passo 1: Preparar Ambiente

```bash
# No servidor CentOS
cd /caminho/para/Maestro

# Dar permissão de execução
chmod +x deploy-linux.sh
```

### Passo 2: Configurar .env

Certifique-se de que o arquivo `.env` contém:
```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SECRET_KEY=...
SESSION_COOKIE_SECURE=True
```

### Passo 3: Deploy

```bash
./deploy-linux.sh --full-deploy
```

O script irá:
- Verificar tudo
- Oferecer abrir portas no firewall (aceite se perguntar)
- Construir e iniciar containers

### Passo 4: Abrir Portas no Fortinet

**⚠️ IMPORTANTE**: Como você usa Fortinet (firewall externo), abra as portas manualmente:

1. Acesse o painel do Fortinet
2. Crie regras para:
   - **Porta 80 (HTTP)** - Permitir TCP:80 → IP do servidor
   - **Porta 443 (HTTPS)** - Permitir TCP:443 → IP do servidor
3. **NÃO abra a porta 8000** (ela é apenas interna)

Para mais detalhes, consulte: `docs/CONFIGURAR_FORTINET.md`

### Passo 5: Configurar DNS

No painel do DNS, criar registro:
```
Tipo: A
Nome: maestro
Valor: IP_DO_SERVIDOR
```

### Passo 6: Configurar SSL

```bash
./deploy-linux.sh --setup-ssl
```

### Passo 7: Verificar

```bash
./deploy-linux.sh --status
```

## ✅ Checklist Pós-Deploy

- [ ] Containers rodando (`./deploy-linux.sh --status`)
- [ ] Portas 80 e 443 abertas no firewall
- [ ] DNS configurado e propagado
- [ ] SSL/HTTPS configurado (`./deploy-linux.sh --setup-ssl`)
- [ ] Aplicação acessível em `https://maestro.opera.security`
- [ ] Domínio mantido (não redireciona para IP)

## 🔍 Verificações

### Verificar Containers

```bash
./deploy-linux.sh --status
```

### Verificar Logs

```bash
./deploy-linux.sh --logs
```

### Verificar Portas

```bash
./deploy-linux.sh --check-ports
```

## ❌ Solução de Problemas

### Erro: Docker Compose não encontrado

```bash
# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Erro: Portas em uso

```bash
# Parar containers
./deploy-linux.sh --stop

# Verificar o que está usando as portas
sudo netstat -tulpn | grep -E '80|443'
```

### Erro: Certificado SSL não obtido

1. Verificar DNS: `dig maestro.opera.security`
2. Verificar firewall: `sudo firewall-cmd --list-services`
3. Verificar logs: `./deploy-linux.sh --logs`

## 📚 Documentação Relacionada

- `docs/CONFIGURACAO_PORTAS.md` - Configuração de portas
- `docs/CONFIGURAR_DNS_HTTPS.md` - Configuração DNS e HTTPS
- `docs/GUIA_RAPIDO.md` - Guia rápido

## 🎯 Resumo

**Comando principal:**
```bash
./deploy-linux.sh --full-deploy
```

**Depois:**
1. Abrir portas 80 e 443 no firewall
2. Configurar DNS
3. `./deploy-linux.sh --setup-ssl`

**Pronto!** 🎉

