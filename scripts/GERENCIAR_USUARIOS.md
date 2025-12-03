# Guia de Gerenciamento de Usuários

Scripts para gerenciar usuários no banco de dados do Maestro.

## 📋 Scripts Disponíveis

### 1. `adicionar_usuario.sh` - Adicionar Novo Usuário
Adiciona um novo usuário ou atualiza a senha de um usuário existente.

**Uso:**
```bash
chmod +x adicionar_usuario.sh
./adicionar_usuario.sh
```

**O que faz:**
- Solicita nome de usuário
- Solicita senha (oculta)
- Solicita confirmação de senha
- Solicita email (opcional)
- Cria o usuário no banco
- Se o usuário já existe, oferece opção de atualizar a senha

**Exemplo:**
```bash
$ ./adicionar_usuario.sh
🔐 ADICIONAR NOVO USUÁRIO
==========================

Digite o nome de usuário: joao.silva
Digite a senha: ********
Confirme a senha: ********
Digite o email (opcional, pressione Enter para pular): joao@empresa.com

📋 Resumo:
   Usuário: joao.silva
   Email: joao@empresa.com

Confirma a criação deste usuário? (s/N): s

⏳ Criando usuário...
✅ Usuário 'joao.silva' criado com sucesso!
   ID do usuário: 2

✅ Operação concluída com sucesso!
```

---

### 2. `listar_usuarios.sh` - Listar Todos os Usuários
Lista todos os usuários cadastrados no banco.

**Uso:**
```bash
chmod +x listar_usuarios.sh
./listar_usuarios.sh
```

**Exemplo de saída:**
```
📋 LISTA DE USUÁRIOS
====================

Total de usuários: 3

ID    Usuário             Email                          Ativo    Criado em            Último Login        
--------------------------------------------------------------------------------------------------------------
1     Opera               ti@opera.security             ✅ Sim    2025-11-11 15:00:00  2025-11-11 18:45:00
2     joao.silva          joao@empresa.com              ✅ Sim    2025-11-11 16:00:00  Nunca
3     maria.santos        maria@empresa.com              ✅ Sim    2025-11-11 17:00:00  2025-11-11 17:30:00
```

---

### 3. `remover_usuario.sh` - Remover Usuário
Remove um usuário do banco de dados.

**Uso:**
```bash
chmod +x remover_usuario.sh
./remover_usuario.sh
```

**⚠️ ATENÇÃO:** Esta ação não pode ser desfeita!

**Exemplo:**
```bash
$ ./remover_usuario.sh
🗑️  REMOVER USUÁRIO
===================

Digite o nome de usuário a ser removido: joao.silva

⚠️  ATENÇÃO: Esta ação não pode ser desfeita!
Confirma a remoção do usuário 'joao.silva'? (s/N): s

⏳ Removendo usuário...
✅ Usuário 'joao.silva' removido com sucesso!

✅ Operação concluída com sucesso!
```

---

### 4. `adicionar_usuario.py` - Versão Python (Local)
Versão Python do script de adicionar usuário, pode ser executada localmente.

**Uso:**
```bash
# Localmente (fora do container)
python3 adicionar_usuario.py

# Ou dentro do container
docker exec -it maestro-portal python3 /app/adicionar_usuario.py
```

**Vantagens:**
- Validação mais robusta
- Interface mais amigável
- Pode ser executado localmente se tiver acesso ao banco

---

## 🔧 Requisitos

- Container `maestro-portal` deve estar rodando
- Arquivo `.env` configurado corretamente
- Acesso ao banco de dados Supabase

---

## 📝 Regras de Validação

### Nome de Usuário:
- Mínimo 3 caracteres
- Máximo 50 caracteres
- Apenas letras, números, ponto (`.`), underscore (`_`) e hífen (`-`)
- Case-sensitive (diferencia maiúsculas de minúsculas)
- Exemplos válidos: `joao.silva`, `maria_santos`, `admin-01`

### Senha:
- Mínimo 6 caracteres
- Máximo 100 caracteres
- Recomendado usar senhas fortes

### Email:
- Opcional
- Deve conter `@`
- Não é validado completamente (apenas verifica se tem `@`)

---

## 🚀 Exemplos de Uso

### Adicionar múltiplos usuários rapidamente:

```bash
# Criar usuário 1
./adicionar_usuario.sh
# Usuário: admin
# Senha: Admin@2026

# Criar usuário 2
./adicionar_usuario.sh
# Usuário: operador
# Senha: Operador@2026
```

### Verificar usuários antes de remover:

```bash
# Listar todos
./listar_usuarios.sh

# Remover se necessário
./remover_usuario.sh
```

### Atualizar senha de usuário existente:

```bash
./adicionar_usuario.sh
# Digite o nome de usuário existente
# O script detectará e oferecerá atualizar a senha
```

---

## ⚠️ Segurança

1. **Senhas são criptografadas** usando bcrypt antes de salvar no banco
2. **Senhas não são exibidas** durante a entrada
3. **Confirmação obrigatória** para operações destrutivas
4. **Logs de auditoria** podem ser verificados no banco (created_at, last_login)

---

## 🐛 Troubleshooting

### Erro: "Container não está rodando"
```bash
# Inicie o container primeiro
./deploy-linux.sh --start
# ou
docker-compose up -d
```

### Erro: "Não foi possível importar auth_manager"
- Certifique-se de que está executando na raiz do projeto
- Verifique se o arquivo `auth.py` existe

### Erro: "Erro ao criar usuário"
- Verifique se o arquivo `.env` está configurado
- Verifique conexão com Supabase
- Verifique se a tabela `maestro_users` existe

---

## 📚 Scripts Relacionados

- `diagnostico_completo.sh` - Diagnóstico completo do sistema
- `verificar_env.sh` - Verificar configuração do .env
- `deploy-linux.sh` - Script de deploy

