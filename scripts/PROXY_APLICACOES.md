# Opções para Acesso às Aplicações via Maestro

## Situação Atual

Atualmente, o Maestro apenas **redireciona** para as URLs das aplicações:
- `http://10.150.16.45:8082/` - Painel de Monitoração Produtiva
- `http://10.150.16.45:5253/` - Dashboard de Perdas
- etc.

**Problema:** Se o Maestro está acessível externamente, mas essas aplicações estão em IPs internos (`10.150.16.45`), elas **NÃO** serão acessíveis externamente.

## Opções Disponíveis

### Opção 1: Expor Portas Individualmente (Atual)
**Como funciona:**
- Cada aplicação mantém sua própria porta exposta
- Maestro apenas redireciona para a URL completa
- Cada aplicação precisa estar acessível externamente

**Vantagens:**
- ✅ Simples de implementar
- ✅ Não precisa modificar o Maestro
- ✅ Cada aplicação funciona independentemente

**Desvantagens:**
- ❌ Precisa expor múltiplas portas no firewall
- ❌ Cada aplicação precisa ter seu próprio domínio/IP público
- ❌ Mais complexo de gerenciar

---

### Opção 2: Proxy Reverso no Maestro (Recomendado)
**Como funciona:**
- Maestro atua como proxy/gateway
- Todas as aplicações são acessadas através do Maestro
- URLs ficam: `http://maestro:8000/app1`, `http://maestro:8000/app2`, etc.

**Vantagens:**
- ✅ Apenas uma porta exposta (8000)
- ✅ Todas as aplicações acessíveis através do Maestro
- ✅ Controle centralizado de acesso
- ✅ Pode adicionar autenticação/unificação
- ✅ Mais seguro (aplicações não expostas diretamente)

**Desvantagens:**
- ⚠️ Precisa configurar proxy reverso
- ⚠️ Pode ter impacto de performance (dependendo do tráfego)

---

### Opção 3: Proxy Reverso Externo (Nginx/Traefik)
**Como funciona:**
- Usa Nginx ou Traefik como proxy reverso
- Maestro e aplicações atrás do proxy
- URLs: `http://maestro/app1`, `http://maestro/app2`

**Vantagens:**
- ✅ Performance melhor (Nginx é otimizado para isso)
- ✅ SSL/HTTPS mais fácil de configurar
- ✅ Load balancing se necessário

**Desvantagens:**
- ⚠️ Precisa instalar e configurar Nginx/Traefik
- ⚠️ Mais complexo de manter

---

## Recomendação: Opção 2 (Proxy no Maestro)

Para seu caso, recomendo a **Opção 2** porque:
1. Você já tem o Maestro funcionando
2. Apenas uma porta exposta
3. Controle centralizado
4. Fácil de implementar

## Implementação ✅ (JÁ IMPLEMENTADO)

Sistema de proxy reverso criado no Maestro que:
- ✅ Mantém as aplicações em IPs internos
- ✅ Acessa através do Maestro: `http://maestro:8000/proxy/painel-monitoracao`
- ✅ Todas as requisições passam pelo Maestro
- ✅ Mantém autenticação unificada
- ✅ Ajusta URLs automaticamente no HTML

## Como Usar

### Configuração no .env

Adicione no arquivo `.env`:

```env
# Usar proxy (True) ou redirecionamento direto (False)
USE_PROXY=True
```

### Comportamento

**Com `USE_PROXY=True` (Recomendado):**
- Aplicações acessadas através do Maestro
- URLs: `http://maestro:8000/proxy/nome-app`
- Apenas porta 8000 precisa estar exposta
- Aplicações não precisam estar acessíveis externamente

**Com `USE_PROXY=False`:**
- Aplicações acessadas diretamente
- URLs: `http://10.150.16.45:8082/` (abre em nova aba)
- Cada aplicação precisa ter sua porta exposta
- Funciona como antes

## Vantagens do Proxy

1. **Segurança:** Aplicações não expostas diretamente
2. **Simplicidade:** Apenas uma porta exposta (8000)
3. **Controle:** Todas as requisições passam pelo Maestro
4. **Autenticação:** Mantém login unificado
5. **Acesso Externo:** Funciona mesmo com IPs internos

## Exemplo de URLs

Com proxy ativado:
- `http://maestro:8000/proxy/painel-monitoracao` → `http://10.150.16.45:8082/`
- `http://maestro:8000/proxy/dashboard-perdas` → `http://10.150.16.45:5253/`
- etc.

## Troubleshooting

### Aplicação não carrega através do proxy
- Verifique se a aplicação está acessível do servidor do Maestro
- Verifique logs: `./deploy-linux.sh --logs`
- Teste acesso direto: `curl http://10.150.16.45:8082/` (no servidor)

### Recursos (CSS/JS) não carregam
- O proxy ajusta URLs automaticamente
- Se ainda não funcionar, pode ser necessário ajustar a aplicação original

