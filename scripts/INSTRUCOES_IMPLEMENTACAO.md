# 📋 Instruções de Implementação - DNS e HTTPS

## ✅ O Que Foi Criado

### 1. Estrutura de Pastas Organizada
```
Maestro/
├── app/              # Código da aplicação (será movido)
├── config/           # Configurações
│   ├── nginx/       # Configurações do Nginx
│   └── ssl/         # Certificados SSL
├── scripts/          # Scripts de deploy
├── docs/             # Documentação
└── logs/             # Logs
```

### 2. Configuração Nginx
- ✅ `config/nginx/nginx.conf` - Configuração HTTPS completa
- ✅ `config/nginx/nginx-http.conf` - Configuração HTTP temporária
- ✅ Headers para manter domínio (não redireciona para IP)
- ✅ Redirecionamento automático HTTP → HTTPS

### 3. Scripts de Automação
- ✅ `scripts/configurar-ssl.sh` - Configura SSL/HTTPS
- ✅ `scripts/renovar-certificado.sh` - Renova certificado
- ✅ `scripts/deploy-completo.sh` - Deploy completo automatizado
- ✅ `scripts/organizar-estrutura.sh` - Reorganiza pastas

### 4. Docker Compose Atualizado
- ✅ Nginx como proxy reverso
- ✅ Suporte a HTTPS
- ✅ Configuração automática baseada em certificado

### 5. Documentação
- ✅ `docs/CONFIGURAR_DNS_HTTPS.md` - Guia completo
- ✅ `docs/GUIA_RAPIDO.md` - Guia rápido
- ✅ `docs/ESTRUTURA_PROJETO.md` - Estrutura de pastas

## 🚀 Como Implementar

### Passo 1: Reorganizar Estrutura (Opcional)

Se quiser usar a nova estrutura de pastas:

```bash
# Executar script de organização
chmod +x scripts/organizar-estrutura.sh
./scripts/organizar-estrutura.sh
```

**OU** mover manualmente:
- `app.py`, `auth.py`, etc. → `app/`
- `templates/` → `app/templates/`
- `static/` → `app/static/`
- Scripts `.sh` → `scripts/`
- Documentação `.md` → `docs/`

### Passo 2: Configurar DNS

No painel do seu provedor de DNS:

1. Criar registro do tipo **A**:
   - **Nome**: `maestro` (ou `@`)
   - **Tipo**: A
   - **Valor**: `186.227.125.170`
   - **TTL**: 3600

2. Aguardar propagação (pode levar até 48h)

3. Verificar:
   ```bash
   dig maestro.opera.security
   # Deve retornar: 186.227.125.170
   ```

### Passo 3: Configurar Firewall

```bash
# Abrir portas 80 e 443
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-services
```

### Passo 4: Atualizar Dockerfile (Se Reorganizou)

Se você reorganizou as pastas, o Dockerfile já está atualizado.  
Se não reorganizou, mantenha o Dockerfile original.

### Passo 5: Deploy

**Opção A - Deploy Automático (Recomendado):**
```bash
chmod +x scripts/*.sh
./scripts/deploy-completo.sh
```

**Opção B - Deploy Manual:**
```bash
# 1. Parar containers
docker-compose down

# 2. Build
docker-compose build

# 3. Iniciar
docker-compose up -d

# 4. Configurar SSL
./scripts/configurar-ssl.sh

# 5. Reiniciar
docker-compose restart
```

### Passo 6: Configurar Renovação Automática

```bash
# Editar crontab
crontab -e

# Adicionar linha (renova todo dia às 3h)
0 3 * * * /caminho/completo/para/Maestro/scripts/renovar-certificado.sh >> /var/log/maestro-ssl-renew.log 2>&1
```

### Passo 7: Verificar

```bash
# Testar HTTPS
curl -I https://maestro.opera.security

# Verificar certificado
openssl s_client -connect maestro.opera.security:443 -servername maestro.opera.security

# Ver logs
docker-compose logs -f nginx
```

## 🔍 Verificações Importantes

### ✅ DNS Funcionando
```bash
dig maestro.opera.security
# Deve retornar: 186.227.125.170
```

### ✅ Certificado SSL Válido
```bash
curl -I https://maestro.opera.security
# Deve retornar: HTTP/2 200 (ou 301/302)
```

### ✅ Domínio Mantido
- Acesse: `https://maestro.opera.security`
- Verifique se a barra de endereço mostra o **domínio** e não o IP
- Verifique se há **cadeado verde** (certificado válido)

### ✅ Headers Corretos
```bash
curl -I https://maestro.opera.security
# Deve mostrar: Host: maestro.opera.security
```

## ❌ Solução de Problemas

### Problema: DNS não resolve
- Aguardar propagação (até 48h)
- Verificar registro DNS no painel
- Limpar cache: `sudo systemd-resolve --flush-caches`

### Problema: Certificado não é obtido
- Verificar DNS: `dig maestro.opera.security`
- Verificar firewall: `sudo firewall-cmd --list-ports`
- Verificar logs: `docker-compose logs nginx`

### Problema: Domínio muda para IP
- Verificar Nginx: `docker-compose exec nginx nginx -t`
- Verificar headers: `curl -I https://maestro.opera.security`
- Limpar cache do navegador

## 📝 Checklist Final

- [ ] DNS configurado e propagado
- [ ] Portas 80 e 443 abertas no firewall
- [ ] Estrutura de pastas organizada (opcional)
- [ ] Dockerfile atualizado (se reorganizou)
- [ ] Deploy executado com sucesso
- [ ] Certificado SSL obtido
- [ ] Nginx configurado com HTTPS
- [ ] Domínio mantido (não redireciona para IP)
- [ ] Renovação automática configurada
- [ ] Testes realizados com sucesso

## 📚 Documentação Adicional

- **Guia Rápido**: `docs/GUIA_RAPIDO.md`
- **Guia Completo**: `docs/CONFIGURAR_DNS_HTTPS.md`
- **Estrutura**: `docs/ESTRUTURA_PROJETO.md`

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker-compose logs -f`
2. Consulte a documentação em `docs/`
3. Verifique a configuração do Nginx: `docker-compose exec nginx nginx -t`

---

**Pronto!** Sua aplicação agora está configurada para manter o domínio e usar HTTPS de forma segura! 🎉

