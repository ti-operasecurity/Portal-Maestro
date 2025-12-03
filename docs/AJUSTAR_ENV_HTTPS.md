# ⚙️ Ajustar .env para HTTPS

## ✅ Resposta Rápida

**Depende do que está no seu .env atual.**

Se você tinha `SESSION_COOKIE_SECURE=False`, precisa mudar para `True`.

## 🔍 O Que Verificar no Seu .env

### Variáveis Importantes para HTTPS

Verifique estas 3 variáveis no seu `.env`:

```env
SESSION_COOKIE_SECURE=???
SESSION_COOKIE_HTTPONLY=???
SESSION_COOKIE_SAMESITE=???
```

## 📋 O Que Precisa Ser Ajustado

### 1. SESSION_COOKIE_SECURE

**Antes (HTTP):**
```env
SESSION_COOKIE_SECURE=False
```

**Agora (HTTPS):**
```env
SESSION_COOKIE_SECURE=True
```

**⚠️ IMPORTANTE**: Esta é a mudança **OBRIGATÓRIA** para HTTPS funcionar corretamente!

### 2. SESSION_COOKIE_HTTPONLY

**Pode manter como estava:**
```env
SESSION_COOKIE_HTTPONLY=True
```

**Ou se não estava definido**, o Docker Compose usa `True` por padrão.

### 3. SESSION_COOKIE_SAMESITE

**Pode manter como estava:**
```env
SESSION_COOKIE_SAMESITE=Lax
```

**Ou se não estava definido**, o Docker Compose usa `Lax` por padrão.

## 🔄 Comparação: Antes vs Agora

### .env Antigo (HTTP)

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave
SECRET_KEY=sua_chave_secreta
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
USE_PROXY=True
```

### .env Novo (HTTPS)

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave
SECRET_KEY=sua_chave_secreta
SESSION_COOKIE_SECURE=True          # ⚠️ MUDOU DE False PARA True
SESSION_COOKIE_HTTPONLY=True        # ✅ Pode manter
SESSION_COOKIE_SAMESITE=Lax         # ✅ Pode manter
USE_PROXY=True                      # ✅ Pode manter
```

## ✅ O Que Você Pode Manter

Você pode manter **TUDO** do seu .env antigo, **EXCETO**:

- ❌ `SESSION_COOKIE_SECURE=False` → Precisa ser `True`
- ✅ `SUPABASE_URL` → Pode manter
- ✅ `SUPABASE_SERVICE_ROLE_KEY` → Pode manter
- ✅ `SECRET_KEY` → Pode manter
- ✅ `SESSION_COOKIE_HTTPONLY` → Pode manter
- ✅ `SESSION_COOKIE_SAMESITE` → Pode manter
- ✅ `USE_PROXY` → Pode manter
- ✅ Qualquer outra variável → Pode manter

## 🔧 Como Ajustar

### Opção 1: Editar Manualmente

```bash
nano .env
```

**Mudar apenas esta linha:**
```env
SESSION_COOKIE_SECURE=True
```

**Salvar**: `Ctrl+X`, depois `Y`, depois `Enter`

### Opção 2: Usar sed (Linux)

```bash
# Se estava False, mudar para True
sed -i 's/SESSION_COOKIE_SECURE=False/SESSION_COOKIE_SECURE=True/' .env

# Verificar se mudou
grep SESSION_COOKIE_SECURE .env
```

### Opção 3: Adicionar se Não Existir

```bash
# Se a linha não existir, adicionar
if ! grep -q "SESSION_COOKIE_SECURE" .env; then
    echo "SESSION_COOKIE_SECURE=True" >> .env
fi
```

## ⚠️ O Que Acontece se Não Ajustar?

### Se `SESSION_COOKIE_SECURE=False` com HTTPS:

- ❌ Cookies não serão marcados como `Secure`
- ❌ Navegadores podem bloquear cookies
- ❌ Sessões podem não funcionar corretamente
- ⚠️ Aplicação pode funcionar, mas com problemas de segurança

### Se `SESSION_COOKIE_SECURE=True` com HTTPS:

- ✅ Cookies são seguros
- ✅ Sessões funcionam corretamente
- ✅ Compatível com todos os navegadores
- ✅ Segurança adequada

## 🧪 Verificar Configuração Atual

```bash
# Ver o que está no .env
grep SESSION_COOKIE .env

# Deve mostrar:
# SESSION_COOKIE_SECURE=True
# SESSION_COOKIE_HTTPONLY=True
# SESSION_COOKIE_SAMESITE=Lax
```

## 📝 Exemplo Completo de .env para HTTPS

```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_key

# Flask Security
SECRET_KEY=sua_chave_secreta_aleatoria_aqui

# Cookies (HTTPS)
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# App
USE_PROXY=True
DEBUG=False
FLASK_ENV=production
```

## ✅ Checklist

- [ ] Verifiquei o .env atual
- [ ] `SESSION_COOKIE_SECURE` está como `True`
- [ ] `SESSION_COOKIE_HTTPONLY` está como `True` (ou não definido)
- [ ] `SESSION_COOKIE_SAMESITE` está como `Lax` (ou não definido)
- [ ] Outras variáveis mantidas como estavam
- [ ] Reiniciarei containers após mudança: `./deploy-linux.sh --restart`

## 🔄 Após Ajustar

```bash
# Reiniciar containers para aplicar mudanças
./deploy-linux.sh --restart

# Ou se preferir, fazer deploy completo novamente
./deploy-linux.sh --full-deploy
```

## 📚 Resumo

**Você pode manter 99% do seu .env antigo!**

**Única mudança necessária:**
- `SESSION_COOKIE_SECURE=False` → `SESSION_COOKIE_SECURE=True`

**Tudo mais pode ficar igual!** ✅

---

**Dica**: Se você não tiver certeza do que está no .env, execute:
```bash
cat .env | grep SESSION_COOKIE
```

