# Formato Correto do Arquivo .env

## ✅ Formato RECOMENDADO (sem aspas):

```env
SUPABASE_URL=https://iglvsnozpiqqhrhyrgax.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnbHZzbm96cGlxcWhyaHl...
SECRET_KEY=minha_chave_secreta_aleatoria_123456
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## ✅ Formato ALTERNATIVO (com aspas - também funciona):

```env
SUPABASE_URL="https://iglvsnozpiqqhrhyrgax.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SECRET_KEY="minha_chave_secreta_aleatoria_123456"
SESSION_COOKIE_SECURE="True"
SESSION_COOKIE_HTTPONLY="True"
SESSION_COOKIE_SAMESITE="Lax"
```

## ⚠️ IMPORTANTE:

1. **NÃO coloque espaços antes ou depois do `=`**
   - ❌ ERRADO: `SUPABASE_URL = https://...`
   - ✅ CORRETO: `SUPABASE_URL=https://...`

2. **Uma variável por linha**

3. **Sem quebras de linha no meio dos valores**

4. **Se usar aspas, use consistentemente** (todas com aspas ou todas sem)

## 📝 Exemplo Completo:

```env
# Configurações do Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_aqui

# Chave secreta (OBRIGATÓRIA)
SECRET_KEY=9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d

# Configurações de Sessão
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## 🔍 Verificar se está correto:

```bash
# Ver conteúdo do .env (sem expor valores completos)
cat .env | sed 's/=.*/=***/' 

# Verificar se não tem espaços extras
cat -A .env | grep "="
```

