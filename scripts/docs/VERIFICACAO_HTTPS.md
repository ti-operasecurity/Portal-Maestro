# ✅ Verificação de Configuração HTTPS

## 🔍 Checklist de Verificação

### 1. Nginx - Redirecionamento HTTP → HTTPS ✅

**Arquivo**: `config/nginx/nginx.conf`

- ✅ Porta 80 redireciona para HTTPS (linha 17)
- ✅ Porta 443 configurada com SSL (linha 22)
- ✅ Certificados SSL configurados (linhas 27-28)
- ✅ Headers de segurança incluídos (HSTS, etc.)

### 2. Docker Compose - Portas Expostas ✅

**Arquivo**: `docker-compose.yml`

- ✅ Porta 80 exposta (linha 43)
- ✅ Porta 443 exposta (linha 44)
- ✅ SESSION_COOKIE_SECURE=True por padrão (linha 17)

### 3. Flask - Detecção de HTTPS ✅

**Arquivo**: `app.py`

- ✅ Detecta HTTPS via `X-Forwarded-Proto` (linha 75)
- ✅ Configura `PREFERRED_URL_SCHEME` como 'https' (linha 52)
- ✅ Atualiza dinamicamente baseado no header do proxy (linha 76)

### 4. Autenticação - Cookies Seguros ✅

**Arquivo**: `auth.py`

- ✅ `SESSION_COOKIE_SECURE` configurado via .env
- ✅ Padrão: `True` (para HTTPS)
- ✅ `SESSION_COOKIE_SAMESITE` configurado como 'Lax' (compatível com HTTPS)

### 5. Scripts - Configuração SSL ✅

**Arquivo**: `scripts/configurar-ssl.sh`

- ✅ Obtém certificado do Let's Encrypt
- ✅ Verifica DNS antes de obter certificado
- ✅ Reinicia containers após obter certificado

## 🧪 Como Testar

### Teste 1: Redirecionamento HTTP → HTTPS

```bash
curl -I http://maestro.opera.security
```

**Esperado**: `HTTP/1.1 301 Moved Permanently` com `Location: https://...`

### Teste 2: Acesso HTTPS

```bash
curl -I https://maestro.opera.security
```

**Esperado**: `HTTP/2 200` ou `HTTP/1.1 200`

### Teste 3: Certificado SSL Válido

```bash
openssl s_client -connect maestro.opera.security:443 -servername maestro.opera.security
```

**Esperado**: Certificado válido do Let's Encrypt

### Teste 4: Headers de Segurança

```bash
curl -I https://maestro.opera.security
```

**Esperado**:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`

### Teste 5: Cookies Seguros

No navegador (DevTools → Application → Cookies):
- `maestro_session` deve ter:
  - ✅ `Secure` marcado
  - ✅ `HttpOnly` marcado
  - ✅ `SameSite=Lax`

## ⚙️ Configuração do .env

Certifique-se de que o `.env` contém:

```env
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## 🔄 Fluxo de Requisição HTTPS

```
1. Cliente → https://maestro.opera.security:443
2. Fortinet → Permite (porta 443 aberta)
3. Nginx → Recebe na porta 443
4. Nginx → Verifica certificado SSL
5. Nginx → Adiciona header X-Forwarded-Proto: https
6. Nginx → Proxy para Flask (porta 8000 interna)
7. Flask → Detecta HTTPS via X-Forwarded-Proto
8. Flask → Configura PREFERRED_URL_SCHEME = 'https'
9. Flask → Usa cookies seguros (SESSION_COOKIE_SECURE=True)
10. Flask → Retorna resposta
11. Nginx → Adiciona headers de segurança (HSTS, etc.)
12. Cliente → Recebe resposta HTTPS segura
```

## ⚠️ Problemas Comuns

### Problema: HTTP não redireciona para HTTPS

**Causa**: Certificado SSL não encontrado, Nginx usando configuração HTTP temporária

**Solução**:
```bash
./deploy-linux.sh --setup-ssl
```

### Problema: Certificado inválido

**Causa**: DNS não configurado ou não propagado

**Solução**:
1. Verificar DNS: `dig maestro.opera.security`
2. Aguardar propagação (1-2 horas)
3. Executar: `./deploy-linux.sh --setup-ssl`

### Problema: Cookies não são seguros

**Causa**: `SESSION_COOKIE_SECURE=False` no .env

**Solução**:
1. Editar `.env`: `SESSION_COOKIE_SECURE=True`
2. Reiniciar containers: `./deploy-linux.sh --restart`

### Problema: Mixed Content (HTTP em página HTTPS)

**Causa**: Recursos carregados via HTTP

**Solução**: 
- Nginx já reescreve URLs para HTTPS
- Verificar se todas as URLs são relativas ou HTTPS

## ✅ Checklist Final

- [ ] Nginx configurado com HTTPS
- [ ] Redirecionamento HTTP → HTTPS funcionando
- [ ] Certificado SSL válido
- [ ] Portas 80 e 443 abertas no Fortinet
- [ ] DNS configurado e propagado
- [ ] `.env` com `SESSION_COOKIE_SECURE=True`
- [ ] Flask detecta HTTPS corretamente
- [ ] Cookies são seguros (Secure=True)
- [ ] Headers de segurança presentes
- [ ] Testes realizados com sucesso

## 📚 Documentação Relacionada

- `docs/CONFIGURAR_DNS_HTTPS.md` - Configuração completa
- `docs/CONFIGURAR_FORTINET.md` - Configuração do firewall
- `docs/SEQUENCIA_DEPLOY.md` - Sequência de deploy

---

**Tudo configurado para HTTPS!** 🔒✅

