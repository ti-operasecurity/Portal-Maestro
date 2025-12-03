# Configuração DNS e HTTPS - Maestro Portal

Este guia explica como configurar o DNS para manter o domínio e ativar HTTPS no Maestro Portal.

## 📋 Pré-requisitos

- Servidor Linux (CentOS) com Docker e Docker Compose instalados
- Domínio `maestro.opera.security` apontando para o IP do servidor
- Portas 80 e 443 abertas no firewall
- Acesso root ou sudo no servidor

## 🌐 Passo 1: Configurar DNS

### Opção A: DNS Externo (Recomendado)

1. Acesse o painel do seu provedor de DNS
2. Crie um registro do tipo **A**:
   - **Nome/Host**: `maestro` (ou `@` para o domínio raiz)
   - **Tipo**: A
   - **Valor/IP**: `186.227.125.170` (seu IP do servidor)
   - **TTL**: 3600 (ou menor para propagação mais rápida)

3. Aguarde a propagação DNS (pode levar de alguns minutos a 48 horas)
4. Verifique se o DNS está funcionando:
   ```bash
   dig maestro.opera.security
   # ou
   nslookup maestro.opera.security
   ```

### Opção B: DNS Local (hosts file)

Se estiver testando localmente, adicione ao `/etc/hosts`:
```
186.227.125.170 maestro.opera.security
```

## 🔒 Passo 2: Configurar HTTPS com Let's Encrypt

### 2.1. Preparar o ambiente

```bash
# Navegar para o diretório do projeto
cd /caminho/para/Maestro

# Dar permissão de execução aos scripts
chmod +x scripts/*.sh

# Criar diretórios necessários
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p logs/nginx
```

### 2.2. Configurar variáveis

Edite o arquivo `.env` e certifique-se de que:
```env
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=Lax
```

### 2.3. Obter certificado SSL

```bash
# Executar script de configuração SSL
./scripts/configurar-ssl.sh
```

O script irá:
1. Verificar se o DNS está configurado
2. Iniciar Nginx temporário
3. Obter certificado do Let's Encrypt
4. Configurar Nginx com HTTPS
5. Reiniciar containers

### 2.4. Configurar renovação automática

Adicione ao crontab para renovar automaticamente:
```bash
# Editar crontab
crontab -e

# Adicionar linha (renova todo dia às 3h da manhã)
0 3 * * * /caminho/para/Maestro/scripts/renovar-certificado.sh >> /var/log/maestro-ssl-renew.log 2>&1
```

## 🔧 Passo 3: Verificar Configuração

### 3.1. Verificar DNS

```bash
# Verificar se o domínio resolve corretamente
dig maestro.opera.security +short
# Deve retornar: 186.227.125.170
```

### 3.2. Verificar HTTPS

```bash
# Testar certificado SSL
openssl s_client -connect maestro.opera.security:443 -servername maestro.opera.security

# Verificar se o domínio é mantido
curl -I https://maestro.opera.security
# O header "Location" não deve conter o IP
```

### 3.3. Testar no navegador

1. Acesse: `https://maestro.opera.security`
2. Verifique se:
   - O domínio permanece na barra de endereço (não muda para IP)
   - O certificado SSL é válido (cadeado verde)
   - A aplicação carrega corretamente

## 🛠️ Solução de Problemas

### Problema: DNS não resolve

**Sintomas**: Navegador mostra IP ao invés do domínio

**Soluções**:
1. Verificar se o registro DNS está correto
2. Aguardar propagação DNS (pode levar até 48h)
3. Limpar cache DNS:
   ```bash
   # Linux
   sudo systemd-resolve --flush-caches
   
   # Windows
   ipconfig /flushdns
   ```

### Problema: Certificado SSL não é obtido

**Sintomas**: Erro ao executar `configurar-ssl.sh`

**Soluções**:
1. Verificar se o DNS está apontando corretamente:
   ```bash
   dig maestro.opera.security
   ```
2. Verificar se as portas 80 e 443 estão abertas:
   ```bash
   sudo firewall-cmd --list-ports
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```
3. Verificar se o Nginx está acessível na porta 80:
   ```bash
   curl http://maestro.opera.security/.well-known/acme-challenge/test
   ```

### Problema: Domínio muda para IP no navegador

**Sintomas**: Ao acessar o domínio, o navegador redireciona para o IP

**Soluções**:
1. Verificar configuração do Nginx:
   ```bash
   docker-compose exec nginx nginx -t
   ```
2. Verificar se os headers estão corretos:
   ```bash
   curl -I https://maestro.opera.security
   # Deve mostrar: Host: maestro.opera.security
   ```
3. Limpar cache do navegador
4. Verificar se há redirecionamentos no código da aplicação

### Problema: Certificado expira

**Sintomas**: Aviso de certificado inválido no navegador

**Soluções**:
1. Renovar manualmente:
   ```bash
   ./scripts/renovar-certificado.sh
   ```
2. Verificar se o crontab está configurado
3. Verificar logs:
   ```bash
   tail -f /var/log/maestro-ssl-renew.log
   ```

## 📝 Configuração Manual do Nginx (Alternativa)

Se preferir configurar manualmente:

1. Edite `config/nginx/nginx.conf`
2. Altere `server_name` para seu domínio
3. Ajuste caminhos dos certificados SSL
4. Reinicie o Nginx:
   ```bash
   docker-compose restart nginx
   ```

## 🔐 Segurança Adicional

### Firewall

```bash
# Permitir apenas portas necessárias
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --remove-service=ssh  # Se não precisar de SSH externo
sudo firewall-cmd --reload
```

### Headers de Segurança

Os headers de segurança já estão configurados no `nginx.conf`:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 📚 Referências

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [DNS Configuration Guide](https://www.cloudflare.com/learning/dns/what-is-dns/)

## ✅ Checklist Final

- [ ] DNS configurado e propagado
- [ ] Certificado SSL obtido e válido
- [ ] Nginx configurado com HTTPS
- [ ] Domínio mantido na barra de endereço
- [ ] Renovação automática configurada
- [ ] Firewall configurado
- [ ] Testes realizados com sucesso

