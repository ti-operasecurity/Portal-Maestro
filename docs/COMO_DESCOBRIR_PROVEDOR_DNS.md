# 🔍 Como Descobrir Onde Está o DNS do Domínio?

## 🎯 Métodos para Descobrir

### Método 1: Verificar WHOIS (Mais Rápido)

```bash
# No servidor ou seu computador
whois opera.security
```

**Procure por:**
- **Registrar**: Nome da empresa que registrou
- **Name Server**: Servidores DNS (ex: `ns1.cloudflare.com`)

### Método 2: Verificar Name Servers

```bash
# Verificar servidores DNS
dig NS opera.security

# Ou
nslookup -type=NS opera.security
```

**Interpretação:**
- Se aparecer `cloudflare.com` → DNS está no Cloudflare
- Se aparecer `godaddy.com` → DNS está no GoDaddy
- Se aparecer `registro.br` → DNS está no Registro.br

### Método 3: Verificar Online

Acesse: https://www.whatsmydns.net/#NS/opera.security

Mostra os servidores DNS atuais.

## 📋 Tabela de Referência

| Name Server | Provedor | Onde Configurar |
|-------------|----------|-----------------|
| `ns1.cloudflare.com` | Cloudflare | https://dash.cloudflare.com |
| `ns*.godaddy.com` | GoDaddy | https://www.godaddy.com |
| `ns*.registro.br` | Registro.br | https://registro.br |
| `ns*.namecheap.com` | Namecheap | https://www.namecheap.com |
| `ns*.amazonaws.com` | AWS Route 53 | Console AWS |
| `ns*.google.com` | Google Domains | https://domains.google.com |

## 🔍 Exemplo Prático

### Passo 1: Verificar WHOIS

```bash
whois opera.security
```

**Saída exemplo:**
```
Registrar: REGISTRO.BR
Name Server: ns1.registro.br
Name Server: ns2.registro.br
```

**Conclusão**: DNS está no **Registro.br**

### Passo 2: Acessar Painel

1. Vá em: https://registro.br
2. Faça login
3. Configure DNS lá

## 🆘 Não Consegue Descobrir?

### Opção 1: Verificar Email

Procure emails de quando o domínio foi registrado:
- Email de confirmação
- Email de renovação
- Email do registrador

### Opção 2: Contatar Administrador

Se o domínio é da empresa:
- Contate o departamento de TI
- Pergunte onde o DNS está configurado
- Peça acesso ao painel

### Opção 3: Verificar Conta da Empresa

- Verifique contas corporativas
- Procure por serviços de domínio
- Verifique faturas/recibos

## 📝 Checklist de Descoberta

- [ ] Executei `whois opera.security`
- [ ] Identifiquei o registrador
- [ ] Verifiquei name servers com `dig NS`
- [ ] Identifiquei o provedor de DNS
- [ ] Acessei o painel correto
- [ ] Encontrei a seção de DNS

## 🎯 Próximo Passo

Após descobrir onde está o DNS:

1. Acesse o painel
2. Faça login
3. Configure o registro A
4. Consulte: `docs/ONDE_CONFIGURAR_DNS.md`

---

**Dica**: Na maioria dos casos, o DNS está no mesmo lugar onde o domínio foi registrado! 🎯

