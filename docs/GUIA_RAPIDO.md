# Guia Rápido - Configurar DNS e HTTPS

## 🎯 Objetivo

Configurar o Maestro Portal para:
1. ✅ Manter o domínio `maestro.opera.security` (não redirecionar para IP)
2. ✅ Ativar HTTPS com certificado SSL válido

## ⚡ Passos Rápidos

### 1. Configurar DNS (5 minutos)

No painel do seu provedor de DNS, crie um registro:

```
Tipo: A
Nome: maestro (ou @)
Valor: 186.227.125.170
TTL: 3600
```

**Verificar DNS:**
```bash
dig maestro.opera.security
# Deve retornar: 186.227.125.170
```

### 2. Preparar Servidor (2 minutos)

```bash
# No servidor CentOS
cd /caminho/para/Maestro

# Dar permissões
chmod +x scripts/*.sh

# Criar diretórios
mkdir -p certbot/conf certbot/www logs/nginx
```

### 3. Configurar Firewall (1 minuto)

```bash
# Abrir portas 80 e 443
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-services
```

### 4. Deploy com HTTPS (5 minutos)

```bash
# Opção A: Deploy completo automático
./scripts/deploy-completo.sh

# Opção B: Passo a passo
# 1. Parar containers
docker-compose down

# 2. Iniciar serviços
docker-compose up -d nginx maestro-portal

# 3. Obter certificado SSL
./scripts/configurar-ssl.sh

# 4. Reiniciar
docker-compose restart
```

### 5. Verificar (2 minutos)

```bash
# Testar HTTPS
curl -I https://maestro.opera.security

# Verificar certificado
openssl s_client -connect maestro.opera.security:443 -servername maestro.opera.security

# Ver logs
docker-compose logs -f nginx
```

## 🔧 Configuração Automática de Renovação

```bash
# Adicionar ao crontab
crontab -e

# Adicionar linha (renova todo dia às 3h)
0 3 * * * /caminho/para/Maestro/scripts/renovar-certificado.sh >> /var/log/maestro-ssl-renew.log 2>&1
```

## ❌ Problemas Comuns

### DNS não resolve
- Aguardar propagação (até 48h)
- Verificar registro DNS no painel
- Limpar cache: `sudo systemd-resolve --flush-caches`

### Certificado não é obtido
- Verificar se DNS está correto: `dig maestro.opera.security`
- Verificar se porta 80 está aberta: `sudo firewall-cmd --list-ports`
- Verificar logs: `docker-compose logs nginx`

### Domínio muda para IP
- Verificar configuração Nginx: `docker-compose exec nginx nginx -t`
- Verificar headers: `curl -I https://maestro.opera.security`
- Limpar cache do navegador

## 📚 Documentação Completa

Para mais detalhes, consulte:
- `docs/CONFIGURAR_DNS_HTTPS.md` - Guia completo
- `docs/ESTRUTURA_PROJETO.md` - Estrutura de pastas

## ✅ Checklist

- [ ] DNS configurado e propagado
- [ ] Portas 80 e 443 abertas no firewall
- [ ] Certificado SSL obtido
- [ ] Nginx configurado com HTTPS
- [ ] Domínio mantido (não redireciona para IP)
- [ ] Renovação automática configurada
- [ ] Testes realizados com sucesso

