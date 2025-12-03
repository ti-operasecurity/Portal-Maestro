# 🌐 Onde Configurar o DNS?

## 📍 Resposta Rápida

**O DNS é configurado no painel do seu provedor de domínio**, não no servidor Linux.

## 🎯 Onde Configurar?

### Opção 1: Painel do Registrador de Domínio

Se você registrou o domínio `opera.security` em um registrador (GoDaddy, Registro.br, Namecheap, etc.), configure lá:

**Exemplos de registradores:**
- **Registro.br** (Brasil)
- **GoDaddy**
- **Namecheap**
- **Cloudflare**
- **Google Domains**
- **Outros registradores**

### Opção 2: Painel do Provedor de DNS

Se você usa um serviço de DNS separado (Cloudflare, Route 53, etc.), configure lá:

**Exemplos:**
- **Cloudflare** (DNS gratuito)
- **AWS Route 53**
- **Google Cloud DNS**
- **Azure DNS**

## 🔍 Como Descobrir Onde Configurar?

### Método 1: Verificar WHOIS

```bash
# No seu computador ou servidor
whois opera.security
```

Procure por:
- **Registrar**: Nome do registrador
- **Name Servers**: Servidores DNS atuais

### Método 2: Verificar no Painel do Domínio

1. Acesse o site onde você comprou/registrou o domínio
2. Faça login
3. Procure por:
   - **DNS Management**
   - **Gerenciamento de DNS**
   - **Zona DNS**
   - **DNS Records**

## 📋 Passo a Passo Genérico

### 1. Acessar o Painel

1. Vá ao site do seu registrador/provedor de DNS
2. Faça login
3. Encontre a seção de **DNS** ou **Gerenciamento de DNS**

### 2. Localizar Zona DNS

Procure por:
- **DNS Zone**
- **Zona DNS**
- **DNS Records**
- **Registros DNS**

### 3. Criar Registro A

1. Clique em **Adicionar Registro** ou **Add Record**
2. Selecione tipo **A**
3. Preencha:
   - **Nome/Host**: `maestro` (ou deixe em branco para o domínio raiz)
   - **Tipo**: `A`
   - **Valor/IP**: `186.227.125.170` (IP do seu servidor)
   - **TTL**: `3600` (ou padrão)

4. Salve

### 4. Aguardar Propagação

- Pode levar de alguns minutos a 48 horas
- Normalmente leva 1-2 horas

## 🌍 Exemplos por Provedor

### Registro.br (Brasil)

1. Acesse: https://registro.br
2. Faça login
3. Vá em **Meus Domínios** → Selecione `opera.security`
4. Clique em **DNS**
5. Adicione registro:
   - **Nome**: `maestro`
   - **Tipo**: `A`
   - **Valor**: `186.227.125.170`
6. Salve

### Cloudflare

1. Acesse: https://dash.cloudflare.com
2. Selecione o domínio `opera.security`
3. Vá em **DNS** → **Records**
4. Clique em **Add record**
5. Preencha:
   - **Type**: `A`
   - **Name**: `maestro`
   - **IPv4 address**: `186.227.125.170`
   - **Proxy**: Desligado (se quiser IP direto)
6. Salve

### GoDaddy

1. Acesse: https://www.godaddy.com
2. Faça login
3. Vá em **Meus Produtos** → **DNS**
4. Clique em **Gerenciar DNS**
5. Role até **Registros**
6. Clique em **Adicionar**
7. Preencha:
   - **Tipo**: `A`
   - **Nome**: `maestro`
   - **Valor**: `186.227.125.170`
   - **TTL**: `1 hora`
8. Salve

### Namecheap

1. Acesse: https://www.namecheap.com
2. Faça login
3. Vá em **Domain List** → Clique em **Manage** no domínio
4. Vá em **Advanced DNS**
5. Clique em **Add New Record**
6. Preencha:
   - **Type**: `A Record`
   - **Host**: `maestro`
   - **Value**: `186.227.125.170`
   - **TTL**: `Automatic`
7. Salve

## 🔍 Verificar se Está Configurado

### No Servidor Linux

```bash
# Verificar se DNS resolve
dig maestro.opera.security

# Ou
nslookup maestro.opera.security

# Deve retornar: 186.227.125.170
```

### Do Seu Computador

```bash
# Windows PowerShell
nslookup maestro.opera.security

# Linux/Mac
dig maestro.opera.security
```

### Online

- https://www.whatsmydns.net
- https://dnschecker.org
- Digite: `maestro.opera.security`

## ⚠️ Importante

### O que NÃO fazer

- ❌ Não configurar DNS no servidor Linux
- ❌ Não editar `/etc/hosts` no servidor (isso é apenas local)
- ❌ Não configurar no Fortinet (ele não gerencia DNS)

### O que fazer

- ✅ Configurar no painel do registrador/provedor de DNS
- ✅ Criar registro tipo A
- ✅ Apontar para o IP do servidor
- ✅ Aguardar propagação

## 📝 Resumo

| Onde Configurar | O que é |
|----------------|---------|
| **Painel do Registrador** | Onde você comprou o domínio |
| **Painel do Provedor DNS** | Se usa Cloudflare, Route 53, etc. |
| ❌ **Servidor Linux** | NÃO configure aqui |
| ❌ **Fortinet** | NÃO gerencia DNS |

## 🎯 Checklist

- [ ] Identifiquei onde o domínio está registrado
- [ ] Acessei o painel do registrador/provedor DNS
- [ ] Encontrei a seção de gerenciamento DNS
- [ ] Criei registro tipo A
- [ ] Nome: `maestro`
- [ ] Valor: IP do servidor (`186.227.125.170`)
- [ ] Salvei a configuração
- [ ] Aguardei propagação (1-2 horas)
- [ ] Verifiquei com `dig` ou `nslookup`

## 🆘 Não Sabe Onde Está o Domínio?

1. **Verificar email**: Procure emails do registrador quando comprou o domínio
2. **Verificar WHOIS**: `whois opera.security`
3. **Contatar administrador**: Se não foi você quem registrou
4. **Verificar empresa**: Se o domínio é da empresa, pode estar no departamento de TI

---

**Lembre-se**: DNS é configurado no **painel do domínio**, não no servidor! 🌐

