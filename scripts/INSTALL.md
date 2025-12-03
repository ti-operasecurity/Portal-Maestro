# Guia de Instalação - Maestro Portal

## Pré-requisitos

- Python 3.8 ou superior
- Conta no Supabase (gratuita)
- Projeto criado no Supabase

## Passo a Passo

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

#### Opção A: Usando o script de setup (Recomendado)

```bash
python setup.py
```

O script irá:
- Solicitar as credenciais do Supabase
- Gerar uma SECRET_KEY segura automaticamente
- Criar o arquivo `.env` com todas as configurações

#### Opção B: Manualmente

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` e preencha:
   - `SUPABASE_URL`: URL do seu projeto Supabase
   - `SUPABASE_SERVICE_ROLE_KEY`: Chave service_role do Supabase
   - `SECRET_KEY`: Gere uma chave aleatória (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - Variáveis de banco (opcionais): `DB_HOST`, `DB_USER`, `DB_PSW`, `DB_PORT`, `DB_NAME`

### 3. Configurar Banco de Dados no Supabase

1. Acesse o [Supabase Dashboard](https://app.supabase.com)
2. Selecione seu projeto
3. Vá em **SQL Editor**
4. Clique em **New Query**
5. Copie e cole o conteúdo do arquivo `supabase_setup.sql`
6. Clique em **Run** para executar

Isso criará:
- Tabela `users` com estrutura completa
- Índices para performance
- Triggers automáticos
- Row Level Security (RLS)

### 4. Criar Usuário de Teste

```bash
python create_test_user.py
```

Isso criará o usuário:
- **Usuário:** Opera
- **Senha:** Opera@2026

### 5. Executar a Aplicação

#### Desenvolvimento Local

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

#### Produção com Docker

```bash
# Build da imagem
docker build -t maestro-portal .

# Executar container
docker run -d -p 5000:5000 \
  --env-file .env \
  --name maestro maestro-portal
```

## Verificação

1. Acesse `http://localhost:5000`
2. Você será redirecionado para `/login`
3. Faça login com:
   - Usuário: `Opera`
   - Senha: `Opera@2026`
4. Após login, você verá o portal principal

## Obtendo Credenciais do Supabase

### SUPABASE_URL
1. No dashboard do Supabase, vá em **Settings** > **API**
2. Copie o valor de **Project URL**

### SUPABASE_SERVICE_ROLE_KEY
1. No mesmo local (Settings > API)
2. Copie o valor de **service_role** `secret` key
3. ⚠️ **IMPORTANTE**: Esta chave tem acesso total. Nunca exponha no frontend!

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'supabase'"
```bash
pip install -r requirements.txt
```

### Erro: "SUPABASE_URL e SUPABASE_KEY devem estar configurados"
- Verifique se o arquivo `.env` existe na raiz do projeto
- Confirme que as variáveis estão corretas
- Reinicie a aplicação

### Erro: "relation 'users' does not exist"
- Execute o script `supabase_setup.sql` no Supabase
- Verifique se a tabela foi criada corretamente

### Erro ao fazer login
- Verifique se o usuário foi criado: `python create_test_user.py`
- Confirme que a senha está correta
- Verifique os logs do Supabase para erros

### Sessão não persiste
- Verifique se `SECRET_KEY` está configurada no `.env`
- Em produção, use HTTPS para `SESSION_COOKIE_SECURE=True`

## Estrutura de Arquivos

```
Maestro/
├── app.py                 # Aplicação Flask principal
├── auth.py                # Módulo de autenticação
├── requirements.txt       # Dependências Python
├── .env                  # Variáveis de ambiente (não commitado)
├── .env.example          # Exemplo de variáveis
├── setup.py              # Script de configuração
├── create_test_user.py   # Script para criar usuário de teste
├── supabase_setup.sql    # Script SQL para criar tabela
├── templates/
│   ├── index.html        # Portal principal
│   └── login.html        # Página de login
└── static/
    ├── css/
    │   ├── style.css     # Estilos do portal
    │   └── login.css     # Estilos do login
    └── images/
        └── logo_opera.png
```

## Segurança

✅ **Implementado:**
- Hash bcrypt com 12 rounds
- Sessões seguras com cookies HTTPOnly
- Proteção CSRF com SameSite
- Row Level Security no Supabase
- Senhas nunca armazenadas em texto plano

⚠️ **Recomendações para Produção:**
- Use HTTPS obrigatoriamente
- Configure rate limiting
- Monitore logs de autenticação
- Use variáveis de ambiente seguras
- Mantenha dependências atualizadas
- Configure backup do banco de dados

## Suporte

Para mais informações, consulte:
- `README_AUTH.md` - Documentação completa de autenticação
- `README.md` - Documentação geral do projeto

