# 🔌 Configuração de Portas - Maestro Portal

## ✅ Configuração Correta

### Portas que DEVEM estar abertas no firewall:
- **Porta 80 (HTTP)** - Para redirecionamento e validação SSL
- **Porta 443 (HTTPS)** - Para acesso seguro à aplicação

### Porta que NÃO deve estar exposta:
- **Porta 8000** - Apenas interna (dentro da rede Docker)

## 📊 Arquitetura de Portas

```
Internet
   ↓
Firewall (portas 80 e 443 abertas)
   ↓
Nginx Container (portas 80:80 e 443:443)
   ↓
Rede Docker Interna
   ↓
Flask Container (porta 8000 - apenas interna)
```

## 🔍 Como Funciona

1. **Porta 8000 (Flask)**: 
   - Roda **apenas dentro da rede Docker**
   - Acessível apenas pelo Nginx
   - **NÃO exposta para o mundo externo**

2. **Portas 80 e 443 (Nginx)**:
   - Expostas para o mundo
   - Nginx recebe requisições nestas portas
   - Faz proxy reverso para Flask na porta 8000 interna

## ⚠️ Problema: Porta 8000 Exposta

Se a porta 8000 estiver exposta no firewall:

### ❌ Problemas:
- Aplicação acessível diretamente sem HTTPS
- Sem headers de segurança do Nginx
- Domínio pode não ser mantido
- Acesso direto bypassa o Nginx

### ✅ Solução: Fechar Porta 8000

## 🛠️ Verificar e Corrigir Firewall

### Verificar Portas Abertas

```bash
# CentOS/RHEL com firewalld
sudo firewall-cmd --list-ports
sudo firewall-cmd --list-all

# Ou verificar iptables
sudo iptables -L -n | grep 8000
```

### Fechar Porta 8000

```bash
# Se estiver usando firewalld
sudo firewall-cmd --permanent --remove-port=8000/tcp
sudo firewall-cmd --reload

# Verificar se foi removida
sudo firewall-cmd --list-ports
```

### Garantir que Apenas 80 e 443 Estão Abertas

```bash
# Adicionar portas corretas (se não estiverem)
sudo firewall-cmd --permanent --add-service=http   # Porta 80
sudo firewall-cmd --permanent --add-service=https  # Porta 443

# Remover porta 8000 (se estiver)
sudo firewall-cmd --permanent --remove-port=8000/tcp

# Recarregar
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-all
```

## ✅ Configuração Ideal do Firewall

```bash
# Verificar configuração atual
sudo firewall-cmd --list-all

# Deve mostrar apenas:
#   services: http https (ou dhcpv6-client ssh se necessário)
#   ports: (nenhuma porta customizada, especialmente não 8000)
```

### Exemplo de Configuração Correta:

```
public (active)
  target: default
  icmp-block-inversion: no
  interfaces: eth0
  sources:
  services: dhcpv6-client http https ssh
  ports:
  protocols:
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
```

**Nota**: `http` = porta 80, `https` = porta 443

## 🔒 Verificar Docker Compose

No `docker-compose.yml`, a configuração está correta:

```yaml
maestro-portal:
  expose:
    - "8000"  # ✅ Apenas exposta na rede Docker (não no host)

nginx:
  ports:
    - "80:80"    # ✅ Exposta para o mundo
    - "443:443"  # ✅ Exposta para o mundo
```

**Diferença importante:**
- `expose`: Porta disponível apenas na rede Docker
- `ports`: Porta mapeada do container para o host (exposta)

## 🧪 Testar Configuração

### 1. Testar se Porta 8000 está Fechada

```bash
# De fora do servidor (de outro computador)
curl http://SEU_IP:8000
# Deve falhar (conexão recusada ou timeout)

# De dentro do servidor
curl http://localhost:8000
# Deve funcionar (acesso interno)
```

### 2. Testar se Portas 80 e 443 Estão Abertas

```bash
# De fora do servidor
curl -I http://maestro.opera.security
# Deve retornar: HTTP/1.1 301 (redirecionamento para HTTPS)

curl -I https://maestro.opera.security
# Deve retornar: HTTP/2 200 (ou outro código de sucesso)
```

### 3. Verificar Acesso Direto à Porta 8000

```bash
# Tentar acessar diretamente (deve falhar)
curl http://maestro.opera.security:8000
# Deve falhar ou retornar erro de conexão
```

## 📝 Checklist de Portas

- [ ] Porta 80 (HTTP) está aberta no firewall
- [ ] Porta 443 (HTTPS) está aberta no firewall
- [ ] Porta 8000 **NÃO** está exposta no firewall
- [ ] Docker Compose usa `expose` para porta 8000 (não `ports`)
- [ ] Nginx está configurado para portas 80 e 443
- [ ] Teste externo: Porta 8000 não acessível
- [ ] Teste externo: Portas 80 e 443 acessíveis

## 🔧 Comandos Úteis

```bash
# Ver todas as portas abertas
sudo firewall-cmd --list-ports
sudo firewall-cmd --list-services

# Ver regras iptables (alternativa)
sudo iptables -L -n -v | grep -E '8000|80|443'

# Ver portas em uso
sudo netstat -tulpn | grep -E '8000|80|443'
# ou
sudo ss -tulpn | grep -E '8000|80|443'

# Verificar se Docker está expondo portas
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

## ⚠️ Importante

**NUNCA** exponha a porta 8000 no firewall quando usar Nginx como proxy reverso!

A porta 8000 deve ser:
- ✅ Acessível apenas dentro da rede Docker
- ✅ Acessível apenas pelo Nginx
- ❌ **NÃO** acessível diretamente da internet

## 🎯 Resumo

| Porta | Tipo | Exposta? | Acesso |
|-------|------|----------|--------|
| 80 | HTTP | ✅ Sim | Internet → Nginx |
| 443 | HTTPS | ✅ Sim | Internet → Nginx |
| 8000 | Flask | ❌ Não | Apenas Nginx → Flask (interno) |

