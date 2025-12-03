# Problema: MacBook não acessa via domínio externo

## Sintomas
- ✅ Funciona no IP interno da empresa
- ❌ Não funciona via domínio externo no MacBook
- ✅ Funciona em outros dispositivos (iPhone, Windows)
- ❌ Não funciona nem no Chrome do MacBook

## Causas Prováveis

### 1. **Validação de Host no Flask**
O Flask pode estar validando o header `Host` e rejeitando requisições com domínio externo.

### 2. **DNS no MacBook**
MacBooks podem ter configurações de DNS diferentes ou cache DNS que não resolve o domínio corretamente.

### 3. **Firewall/Proxy Reverso**
Se houver um proxy reverso (nginx, Apache) na frente, pode estar bloqueando ou não repassando headers corretamente.

### 4. **Headers Host Removidos**
O código estava removendo o header `Host` completamente, o que pode causar problemas em alguns navegadores.

## Correções Implementadas

### 1. **Configuração Flask para Aceitar Qualquer Host**
```python
app.config['SERVER_NAME'] = None  # Aceita qualquer host/domínio
app.config['PREFERRED_URL_SCHEME'] = 'http'
```

### 2. **Preservar Header Host Quando Necessário**
- Não remover `Host` completamente
- Manter `Host` original para requisições internas
- Remover apenas se for o host do próprio Maestro

### 3. **CORS com Suporte a Host**
- Incluir `Host` nos headers permitidos
- Adicionar `Host` no header `Vary`
- Header `X-Requested-Host` para debug

### 4. **Logging de Debug**
- Log de todas as requisições com Host, Origin, Remote IP
- Ajuda a identificar problemas de acesso externo

## Como Testar

### 1. **Verificar DNS no MacBook**
```bash
# No Terminal do MacBook
nslookup seu-dominio.com
dig seu-dominio.com
```

### 2. **Testar Conexão Direta**
```bash
# No Terminal do MacBook
curl -v http://seu-dominio.com:8000/login
curl -v http://IP_DO_SERVIDOR:8000/login
```

### 3. **Verificar Headers**
```bash
# Ver quais headers estão sendo enviados
curl -I http://seu-dominio.com:8000/login
```

### 4. **Verificar Logs do Servidor**
```bash
docker-compose logs -f maestro-portal
# Procurar por requisições do MacBook
```

### 5. **Testar com IP Direto**
Se funcionar com IP mas não com domínio:
- Problema é DNS ou configuração de proxy reverso
- Verificar se o domínio está apontando para o IP correto

## Troubleshooting Adicional

### Se ainda não funcionar:

1. **Verificar Proxy Reverso (se houver)**
   - Nginx/Apache na frente do Docker
   - Verificar se está repassando headers corretamente
   - Verificar se está bloqueando requisições do MacBook

2. **Verificar Firewall**
   - Porta 8000 aberta para acesso externo?
   - Regras específicas para MacBooks?

3. **Verificar Configurações de Rede do MacBook**
   - VPN ativa?
   - Proxy configurado?
   - DNS customizado?

4. **Testar com Outro Navegador no MacBook**
   - Firefox
   - Safari
   - Chrome (modo anônimo)

5. **Limpar Cache DNS do MacBook**
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

6. **Verificar se o Domínio Resolve Corretamente**
   ```bash
   # No MacBook
   ping seu-dominio.com
   # Deve retornar o IP do servidor
   ```

## Configurações Adicionais Necessárias

Se houver um proxy reverso (nginx/Apache) na frente, adicione:

### Nginx
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Origin $scheme://$host;
    }
}
```

### Variáveis de Ambiente (.env)
```env
# Garantir que aceita qualquer host
SERVER_NAME=
PREFERRED_URL_SCHEME=http
```

## Logs para Debug

Ative logging DEBUG temporariamente:
```python
# No app.py, adicionar:
import logging
logging.basicConfig(level=logging.DEBUG)
```

Ou via variável de ambiente:
```env
DEBUG=True
FLASK_ENV=development
```

## Próximos Passos

1. Reconstruir container com as correções
2. Testar acesso via domínio no MacBook
3. Verificar logs para identificar o problema específico
4. Se necessário, verificar configuração de proxy reverso/firewall

