# ⚡ Deploy Rápido - Sequência de Comandos

## 🎯 Sequência Completa (Copy & Paste)

```bash
# ============================================
# 1. CONECTAR NO SERVIDOR
# ============================================
ssh usuario@IP_DO_SERVIDOR
cd /caminho/para/Maestro

# ============================================
# 2. VERIFICAR ARQUIVOS
# ============================================
ls -la docker-compose.yml .env deploy-linux.sh

# ============================================
# 3. CONFIGURAR .ENV (se necessário)
# ============================================
# Se não existir, criar:
cp env_template.txt .env
nano .env

# Editar com suas configurações:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - SECRET_KEY

# ============================================
# 4. DAR PERMISSÕES
# ============================================
chmod +x deploy-linux.sh
chmod +x scripts/*.sh 2>/dev/null || true

# ============================================
# 5. VERIFICAR DOCKER
# ============================================
docker --version
docker-compose --version || docker compose version
sudo systemctl start docker
sudo systemctl status docker

# ============================================
# 6. EXECUTAR DEPLOY COMPLETO
# ============================================
./deploy-linux.sh --full-deploy

# ============================================
# 7. VERIFICAR STATUS
# ============================================
./deploy-linux.sh --status

# ============================================
# 8. ABRIR PORTAS NO FORTINET (MANUAL)
# ============================================
# Acesse o painel do Fortinet e abra:
# - Porta 80 (HTTP) → IP do servidor
# - Porta 443 (HTTPS) → IP do servidor
# NÃO abra a porta 8000!

# ============================================
# 9. CONFIGURAR DNS
# ============================================
# No painel do DNS, criar registro A:
# Nome: maestro
# Valor: IP do servidor

# ============================================
# 10. CONFIGURAR SSL/HTTPS
# ============================================
./deploy-linux.sh --setup-ssl

# ============================================
# 11. CONFIGURAR RENOVAÇÃO AUTOMÁTICA
# ============================================
crontab -e
# Adicionar linha:
# 0 3 * * * /caminho/completo/para/Maestro/scripts/renovar-certificado.sh >> /var/log/maestro-ssl-renew.log 2>&1

# ============================================
# 12. VERIFICAR TUDO
# ============================================
./deploy-linux.sh --status
curl -I https://maestro.opera.security
```

## 📋 Comandos Essenciais

### Deploy Inicial
```bash
chmod +x deploy-linux.sh
./deploy-linux.sh --full-deploy
```

### Após Abrir Portas no Fortinet
```bash
./deploy-linux.sh --status
```

### Após Configurar DNS
```bash
./deploy-linux.sh --setup-ssl
```

### Verificar Tudo
```bash
./deploy-linux.sh --status
./deploy-linux.sh --logs
```

## ⚠️ Importante

1. **Antes do deploy**: Configure o arquivo `.env`
2. **Após o deploy**: Abra portas 80 e 443 no Fortinet
3. **Após DNS**: Execute `--setup-ssl`
4. **Nunca**: Abra a porta 8000 no Fortinet

## 🆘 Comandos de Emergência

```bash
# Parar tudo
./deploy-linux.sh --stop

# Reiniciar
./deploy-linux.sh --restart

# Ver logs
./deploy-linux.sh --logs

# Verificar portas
./deploy-linux.sh --check-ports
```

---

**Documentação completa**: `docs/SEQUENCIA_DEPLOY.md`

