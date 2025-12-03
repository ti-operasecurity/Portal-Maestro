# 🔒 Abrir Portas no Fortinet - Passo a Passo

## 📋 Portas Necessárias

### ✅ Portas que DEVEM estar abertas:

1. **Porta 80 (HTTP)**
   - Protocolo: TCP
   - Destino: IP do servidor (10.150.16.45)
   - Direção: Entrada (Inbound)
   - Ação: Permitir

2. **Porta 443 (HTTPS)**
   - Protocolo: TCP
   - Destino: IP do servidor (10.150.16.45)
   - Direção: Entrada (Inbound)
   - Ação: Permitir

### ❌ Porta que NÃO deve estar aberta:

- **Porta 8000** - NÃO abrir (é apenas interna no Docker)

## 🔧 Como Abrir no Fortinet

### Via Interface Web (FortiGate)

1. **Acesse o FortiGate**
   - URL: `https://IP_DO_FORTINET` ou `https://fortinet.opera.security`
   - Faça login

2. **Criar Política de Firewall**
   - Vá em **Policy & Objects** → **Firewall Policy**
   - Clique em **Create New**

3. **Regra para Porta 80 (HTTP)**
   - **Name**: `Maestro-HTTP` ou `Maestro-Porta-80`
   - **Incoming Interface**: Selecione a interface externa
   - **Outgoing Interface**: Selecione a interface interna
   - **Source**: `all` ou `any`
   - **Destination**: 
     - Type: `Address`
     - Address: `10.150.16.45` (IP do servidor)
   - **Service**: `HTTP` ou `TCP/80`
   - **Action**: `ACCEPT` ou `Allow`
   - **Schedule**: `always`
   - **Status**: `Enable`
   - Clique em **OK**

4. **Regra para Porta 443 (HTTPS)**
   - **Name**: `Maestro-HTTPS` ou `Maestro-Porta-443`
   - **Incoming Interface**: Selecione a interface externa
   - **Outgoing Interface**: Selecione a interface interna
   - **Source**: `all` ou `any`
   - **Destination**: 
     - Type: `Address`
     - Address: `10.150.16.45` (IP do servidor)
   - **Service**: `HTTPS` ou `TCP/443`
   - **Action**: `ACCEPT` ou `Allow`
   - **Schedule**: `always`
   - **Status**: `Enable`
   - Clique em **OK**

5. **Ordem das Regras**
   - Certifique-se de que as regras do Maestro estão **ANTES** de qualquer regra de bloqueio geral
   - Arraste as regras para o topo se necessário

6. **Aplicar Mudanças**
   - Clique em **Apply** ou **OK**
   - As mudanças são aplicadas automaticamente

### Via CLI (FortiGate)

```bash
# Conectar via SSH no FortiGate
ssh admin@IP_DO_FORTINET

# Entrar no modo de configuração
config firewall policy

# Criar regra HTTP
edit 0
    set name "Maestro-HTTP"
    set srcintf "wan1"  # Ajuste para sua interface externa
    set dstintf "lan"   # Ajuste para sua interface interna
    set srcaddr "all"
    set dstaddr "10.150.16.45"
    set action accept
    set schedule "always"
    set service "HTTP"
    set status enable
next

# Criar regra HTTPS
edit 0
    set name "Maestro-HTTPS"
    set srcintf "wan1"  # Ajuste para sua interface externa
    set dstintf "lan"   # Ajuste para sua interface interna
    set srcaddr "all"
    set dstaddr "10.150.16.45"
    set action accept
    set schedule "always"
    set service "HTTPS"
    set status enable
next
end

# Aplicar
write
```

## ✅ Verificar se Funcionou

### Teste 1: Do Servidor

```bash
# Verificar se portas estão abertas (do servidor)
curl -I http://localhost:80
curl -I https://localhost:443
```

### Teste 2: De Fora do Servidor

De outro computador na rede:

```bash
# Testar porta 80
curl -I http://10.150.16.45

# Testar porta 443
curl -I https://10.150.16.45
```

### Teste 3: Verificar no Fortinet

No FortiGate, vá em **Policy & Objects** → **Firewall Policy** e verifique:
- ✅ Regras estão ativas (Status: Enable)
- ✅ Ordem está correta (antes de regras de bloqueio)
- ✅ Destino está correto (10.150.16.45)

## 📝 Após Abrir as Portas

### 1. Verificar Build do Docker

Se o build ainda estiver rodando, deixe terminar. Se já terminou:

```bash
# Verificar status
./deploy-linux.sh --status

# Se containers não estiverem rodando, iniciar
./deploy-linux.sh --start
```

### 2. Testar Acesso

```bash
# Testar HTTP (deve redirecionar para HTTPS)
curl -I http://10.150.16.45

# Testar HTTPS (após configurar SSL)
curl -I https://10.150.16.45
```

### 3. Configurar SSL (Após DNS)

```bash
# Após configurar DNS e aguardar propagação
./deploy-linux.sh --setup-ssl
```

## ⚠️ Importante

- **Porta 80**: Necessária para obter certificado SSL (Let's Encrypt)
- **Porta 443**: Necessária para HTTPS funcionar
- **Porta 8000**: NÃO abrir (é apenas interna)

## 🔍 Troubleshooting

### Problema: Portas abertas mas não funciona

1. Verificar ordem das regras no Fortinet
2. Verificar se há NAT configurado
3. Verificar se containers estão rodando: `./deploy-linux.sh --status`

### Problema: Porta 80 funciona mas 443 não

1. Verificar se regra HTTPS está ativa
2. Verificar se porta 443 está correta
3. Verificar logs: `./deploy-linux.sh --logs`

---

**Após abrir as portas, execute:**
```bash
./deploy-linux.sh --status
```

Para verificar se tudo está funcionando! ✅

