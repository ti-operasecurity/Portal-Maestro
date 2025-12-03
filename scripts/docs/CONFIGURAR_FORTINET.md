# 🔒 Configuração do Firewall Fortinet

## Visão Geral

O Maestro Portal precisa que as portas **80** (HTTP) e **443** (HTTPS) estejam abertas no firewall Fortinet para acesso externo.

## ⚠️ Importante

- ✅ **Porta 80 (HTTP)** - DEVE estar aberta
- ✅ **Porta 443 (HTTPS)** - DEVE estar aberta
- ❌ **Porta 8000** - NÃO deve estar aberta (é apenas interna)

## 📋 Configuração no Fortinet

### 1. Identificar IP do Servidor

No servidor, execute:
```bash
hostname -I
# ou
ip route get 1.1.1.1 | awk '{print $7; exit}'
```

Anote o IP do servidor (exemplo: `186.227.125.170`)

### 2. Criar Regras no Fortinet

#### Regra 1: Porta 80 (HTTP)

1. Acesse o painel do Fortinet
2. Vá em **Firewall Policies** ou **Políticas de Firewall**
3. Crie uma nova regra:
   - **Nome**: `Maestro-HTTP` ou `Maestro-Porta-80`
   - **Source**: `all` ou `any`
   - **Destination**: IP do servidor (ex: `186.227.125.170`)
   - **Service**: `HTTP` ou `TCP/80`
   - **Action**: `Allow` / `Permitir`
   - **Schedule**: `always`
   - **Status**: `Enabled`

#### Regra 2: Porta 443 (HTTPS)

1. Crie outra regra:
   - **Nome**: `Maestro-HTTPS` ou `Maestro-Porta-443`
   - **Source**: `all` ou `any`
   - **Destination**: IP do servidor (ex: `186.227.125.170`)
   - **Service**: `HTTPS` ou `TCP/443`
   - **Action**: `Allow` / `Permitir`
   - **Schedule**: `always`
   - **Status**: `Enabled`

### 3. Ordem das Regras

Certifique-se de que as regras do Maestro estão **antes** de qualquer regra de bloqueio geral.

### 4. Aplicar e Salvar

- Aplique as mudanças
- Salve a configuração
- Verifique se as regras estão ativas

## 🧪 Verificar Configuração

### Teste 1: Verificar se Porta 80 está Acessível

De fora do servidor (de outro computador):
```bash
curl -I http://IP_DO_SERVIDOR
# Deve retornar: HTTP/1.1 301 ou HTTP/1.1 200
```

### Teste 2: Verificar se Porta 443 está Acessível

```bash
curl -I https://IP_DO_SERVIDOR
# Deve retornar: HTTP/2 200 ou outro código de sucesso
```

### Teste 3: Verificar se Porta 8000 está Fechada (Correto)

```bash
curl http://IP_DO_SERVIDOR:8000
# Deve falhar (timeout ou conexão recusada)
```

## 📝 Exemplo de Configuração

### Via CLI do Fortinet

```bash
# Criar regra HTTP
config firewall policy
    edit 0
        set name "Maestro-HTTP"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "186.227.125.170"
        set action accept
        set schedule "always"
        set service "HTTP"
        set status enable
    next
end

# Criar regra HTTPS
config firewall policy
    edit 0
        set name "Maestro-HTTPS"
        set srcintf "any"
        set dstintf "any"
        set srcaddr "all"
        set dstaddr "186.227.125.170"
        set action accept
        set schedule "always"
        set service "HTTPS"
        set status enable
    next
end
```

## ⚠️ Segurança

### Boas Práticas

1. **Restringir Origem (Opcional)**
   - Se possível, restrinja o `Source` para IPs específicos ou redes internas
   - Exemplo: `Source: 10.0.0.0/8` (apenas rede interna)

2. **Logs**
   - Ative logging nas regras para monitoramento
   - Configure alertas se necessário

3. **NAT (se necessário)**
   - Se o servidor estiver em rede privada, configure NAT no Fortinet
   - Mapeie IP público → IP privado do servidor

## 🔍 Troubleshooting

### Problema: Porta não está acessível

**Verificações:**
1. Regra está ativa no Fortinet?
2. Ordem das regras está correta?
3. IP do servidor está correto?
4. Servidor está rodando? (`./deploy-linux.sh --status`)

### Problema: Timeout na conexão

**Possíveis causas:**
1. Regra bloqueada por outra regra mais restritiva
2. NAT não configurado (se servidor em rede privada)
3. Roteamento incorreto

### Problema: Porta 8000 acessível (não deveria)

**Solução:**
1. Remova qualquer regra que permita porta 8000
2. A porta 8000 deve ser apenas interna (Docker)

## 📚 Referências

- [Documentação Fortinet](https://docs.fortinet.com/)
- [Fortinet Firewall Policies](https://docs.fortinet.com/document/fortigate/latest/administration-guide/1094/firewall-policy)

## ✅ Checklist

- [ ] IP do servidor identificado
- [ ] Regra para porta 80 criada e ativa
- [ ] Regra para porta 443 criada e ativa
- [ ] Porta 8000 NÃO está aberta
- [ ] Regras aplicadas e salvas
- [ ] Testes de conectividade realizados
- [ ] Aplicação acessível externamente

---

**Nota**: Se você não tem acesso ao Fortinet, entre em contato com o administrador de rede para abrir as portas.

