# 🔧 Configurar Fortinet para Build Docker

## ❌ Problema Atual

O Fortinet está **inspecionando/modificando** o tráfego HTTP/HTTPS para os repositórios Debian, causando:
- **Hash Sum mismatch** (pacotes corrompidos)
- **Bad header line** (headers HTTP modificados)
- **Build travado** (downloads falhando continuamente)

## ✅ Solução: Configurar Exceções no Fortinet

### Opção 1: Desabilitar Inspeção SSL/HTTP para Repositórios Debian (Recomendado)

#### Via Interface Web (FortiGate)

1. **Acesse o FortiGate**
   - URL: `https://IP_DO_FORTINET` ou `https://fortinet.opera.security`
   - Faça login

2. **Criar Perfil de Proxy Exceção**
   - Vá em **Policy & Objects** → **Proxy Options** → **Proxy Options Profile**
   - Clique em **Create New**
   - **Name**: `Docker-Build-Exempt`
   - **HTTP Options**:
     - ✅ Marque **Exempt from HTTP Proxy**
   - **HTTPS Options**:
     - ✅ Marque **Exempt from HTTPS Proxy**
   - Clique em **OK**

3. **Criar Política de Firewall com Exceção**
   - Vá em **Policy & Objects** → **Firewall Policy**
   - Clique em **Create New**
   - **Name**: `Docker-Build-Repositories`
   - **Incoming Interface**: Selecione a interface interna (LAN)
   - **Outgoing Interface**: Selecione a interface externa (WAN)
   - **Source**: 
     - Type: `Address`
     - Address: `10.150.16.45` (IP do servidor)
   - **Destination**:
     - Type: `FQDN` ou `Address Group`
     - Adicione os seguintes domínios:
       - `deb.debian.org`
       - `security.debian.org`
       - `*.debian.org`
   - **Service**: `ALL` ou `HTTP, HTTPS`
   - **Action**: `ACCEPT`
   - **Proxy Options**: Selecione o perfil `Docker-Build-Exempt` criado acima
   - **Schedule**: `always`
   - **Status**: `Enable`
   - **Ordem**: Coloque esta regra **ANTES** de outras regras de proxy/inspeção
   - Clique em **OK**

4. **Aplicar Mudanças**
   - Clique em **Apply** ou **OK**

#### Via CLI (FortiGate)

```bash
# Conectar via SSH no FortiGate
ssh admin@IP_DO_FORTINET

# Criar perfil de proxy com exceção
config firewall proxy-options-profile
    edit "Docker-Build-Exempt"
        set http-exempt enable
        set https-exempt enable
    next
end

# Criar política de firewall
config firewall policy
    edit 0
        set name "Docker-Build-Repositories"
        set srcintf "lan"  # Ajuste para sua interface interna
        set dstintf "wan1"  # Ajuste para sua interface externa
        set srcaddr "10.150.16.45"  # IP do servidor
        set dstaddr "deb.debian.org" "security.debian.org"
        set action accept
        set schedule "always"
        set service "ALL"
        set proxy-options-profile "Docker-Build-Exempt"
        set status enable
    next
end

# Aplicar
write
```

### Opção 2: Desabilitar Inspeção SSL/HTTP Globalmente (Menos Seguro)

⚠️ **ATENÇÃO**: Isso reduz a segurança do firewall. Use apenas se a Opção 1 não funcionar.

#### Via Interface Web

1. **Acesse Security Profiles**
   - Vá em **Security Profiles** → **SSL Inspection**
   - Desabilite **SSL Inspection** para tráfego de repositórios Debian

2. **Ou criar exceção por destino**
   - Vá em **Security Profiles** → **SSL Inspection** → **SSL Inspection Profile**
   - Crie um perfil que **não inspeciona** `*.debian.org`

### Opção 3: Whitelist de Domínios Debian

Adicione os seguintes domínios à **whitelist** do Fortinet:

```
deb.debian.org
security.debian.org
*.debian.org
*.debian.net
```

#### Como Adicionar Whitelist

1. **Via Interface Web**
   - Vá em **Security Profiles** → **Web Filter** → **URL Filter**
   - Crie uma categoria `Debian-Repositories`
   - Adicione os domínios acima
   - Marque como **Allow**

2. **Via Firewall Policy**
   - Na política de firewall, adicione os domínios como **Destination Address**
   - Configure para **não inspecionar** estes destinos

## 🔍 Verificar Configuração

Após configurar, teste:

```bash
# No servidor, testar conexão
curl -I http://deb.debian.org/debian/

# Se retornar "200 OK" sem erros, está funcionando
```

## 📋 Domínios que Precisam ser Liberados

Adicione estes domínios à whitelist/exceção:

```
deb.debian.org
security.debian.org
*.debian.org
*.debian.net
cdn-fastly.deb.debian.org
deb.debian.org
ftp.debian.org
```

## ⚙️ Configurações Específicas por Tipo de Inspeção

### Se Fortinet usa Deep Packet Inspection (DPI)

1. **Desabilitar DPI para repositórios Debian**
   - Vá em **Security Profiles** → **Application Control**
   - Crie exceção para `*.debian.org`

### Se Fortinet usa SSL Inspection

1. **Desabilitar SSL Inspection para repositórios Debian**
   - Vá em **Security Profiles** → **SSL Inspection**
   - Crie perfil que não inspeciona `*.debian.org`

### Se Fortinet usa Web Filtering

1. **Permitir repositórios Debian**
   - Vá em **Security Profiles** → **Web Filter**
   - Adicione `*.debian.org` à whitelist

## 🚀 Após Configurar

1. **Aguardar 2-3 minutos** para propagação das regras
2. **Testar build novamente:**
   ```bash
   docker build --network=host -t maestro-maestro-portal:latest .
   ```
3. **Se funcionar**, os downloads devem completar sem "Hash Sum mismatch"

## 📝 Nota Importante

- **Não desabilite a segurança globalmente** - apenas para repositórios Debian
- **Mantenha outras proteções ativas** (antivírus, IPS, etc.)
- **Teste após configurar** para garantir que funciona

## 🔧 Troubleshooting

### Se ainda houver problemas:

1. **Verificar ordem das regras**
   - A regra de exceção deve estar **ANTES** de regras de inspeção

2. **Verificar logs do Fortinet**
   - Vá em **Log & Report** → **Traffic Logs**
   - Procure por bloqueios de `deb.debian.org`

3. **Testar conexão direta**
   ```bash
   curl -v http://deb.debian.org/debian/
   ```

4. **Verificar se há proxy intermediário**
   - Se houver, configure exceção no proxy também

## ✅ Resumo Rápido

**O que fazer:**
1. Criar política de firewall que **não inspeciona** tráfego para `*.debian.org`
2. Adicionar `deb.debian.org` e `security.debian.org` à whitelist
3. Colocar regra **antes** de outras regras de inspeção
4. Testar build novamente

**Resultado esperado:**
- Downloads completam sem "Hash Sum mismatch"
- Build do Docker funciona normalmente
- Aplicação sobe com sucesso

