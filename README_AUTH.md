# Sistema de Autenticação - Maestro

## Configuração Inicial

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Supabase Configuration
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_key

# Flask Security
SECRET_KEY=sua_chave_secreta_aleatoria_aqui
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Database (PostgreSQL - se necessário)
DB_HOST=seu_db_host
DB_USER=seu_db_user
DB_PSW=sua_senha_db
DB_PORT=5432
DB_NAME=seu_db_name
```

**Importante:**
- `SUPABASE_URL`: URL do seu projeto Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Chave service_role do Supabase (para operações administrativas)
- `SECRET_KEY`: Gere uma chave secreta aleatória e segura (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- Variáveis de banco (DB_*): Configurações opcionais para PostgreSQL tradicional, se necessário

### 2. Criar Tabela no Supabase

1. Acesse o SQL Editor no painel do Supabase
2. Execute o conteúdo do arquivo `supabase_setup.sql`
3. Isso criará a tabela `users` com todas as configurações necessárias

### 3. Criar Usuário de Teste

Execute o script para criar o usuário de teste:

```bash
python create_test_user.py
```

Isso criará o usuário:
- **Usuário:** Opera
- **Senha:** Opera@2026

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

## Segurança Implementada

### Criptografia
- **Bcrypt** com 12 rounds para hash de senhas
- Senhas nunca são armazenadas em texto plano
- Hash seguro e resistente a ataques de força bruta

### Sessões
- Sessões seguras com cookies HTTPOnly
- Cookies SameSite para proteção CSRF
- Cookies Secure em produção (HTTPS)
- Sessões permanentes com timeout configurável

### Proteção de Rotas
- Decorator `@login_required` para proteger rotas
- Redirecionamento automático para login se não autenticado
- Verificação de sessão em todas as rotas protegidas

### Banco de Dados
- Row Level Security (RLS) habilitado
- Índices para performance
- Triggers para atualização automática de timestamps
- Validação de dados no banco

## Estrutura de Autenticação

### Arquivos Principais

- `auth.py`: Módulo de autenticação com Supabase
- `app.py`: Rotas Flask com proteção
- `templates/login.html`: Interface de login
- `static/css/login.css`: Estilos do login

### Rotas

- `GET /login`: Exibe página de login
- `POST /login`: Processa autenticação
- `GET /logout`: Encerra sessão
- `GET /`: Página principal (protegida)

## Uso

### Login
1. Acesse `/login`
2. Digite usuário e senha
3. Será redirecionado para a página principal

### Logout
1. Acesse `/logout`
2. Sessão será encerrada
3. Será redirecionado para login

## Produção

### Checklist de Segurança

- [ ] `SECRET_KEY` alterada para valor aleatório forte
- [ ] `SESSION_COOKIE_SECURE=True` (requer HTTPS)
- [ ] HTTPS configurado no servidor
- [ ] Variáveis de ambiente não commitadas no Git
- [ ] RLS configurado corretamente no Supabase
- [ ] Service role key protegida (nunca expor no frontend)
- [ ] Rate limiting configurado (recomendado)
- [ ] Logs de autenticação monitorados

### Docker

O Dockerfile já está configurado. Para produção:

```bash
docker build -t maestro-portal .
docker run -d -p 5000:5000 \
  -e SUPABASE_URL=... \
  -e SUPABASE_KEY=... \
  -e SECRET_KEY=... \
  --name maestro maestro-portal
```

Ou use um arquivo `.env` com docker-compose.

## Troubleshooting

### Erro: "SUPABASE_URL e SUPABASE_KEY devem estar configurados"
- Verifique se o arquivo `.env` existe
- Confirme que as variáveis estão corretas
- Reinicie a aplicação após alterar `.env`

### Erro: "Tabela users não existe"
- Execute o script `supabase_setup.sql` no Supabase
- Verifique se a tabela foi criada corretamente

### Erro ao fazer login
- Verifique se o usuário existe no banco
- Confirme que a senha está correta
- Verifique os logs do Supabase para erros

### Sessão não persiste
- Verifique `SECRET_KEY` no `.env`
- Confirme configurações de cookies
- Em produção, use HTTPS

