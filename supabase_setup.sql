-- Script SQL para criar a tabela de usuários no Supabase
-- Execute este script no SQL Editor do Supabase
-- Nome da tabela: maestro_users

-- Remove a tabela se já existir (CUIDADO: isso apagará todos os dados!)
-- Descomente a linha abaixo apenas se quiser recriar a tabela do zero
-- DROP TABLE IF EXISTS maestro_users CASCADE;

-- Cria a tabela de usuários (se não existir)
CREATE TABLE IF NOT EXISTS maestro_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Adiciona colunas se não existirem (para atualizações incrementais)
DO $$ 
BEGIN
    -- Adiciona username se não existir (sem NOT NULL primeiro)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='username') THEN
        ALTER TABLE maestro_users ADD COLUMN username VARCHAR(100);
        -- Atualiza valores NULL se houver
        UPDATE maestro_users SET username = 'user_' || id WHERE username IS NULL;
        -- Agora adiciona NOT NULL e UNIQUE
        ALTER TABLE maestro_users ALTER COLUMN username SET NOT NULL;
        ALTER TABLE maestro_users ADD CONSTRAINT maestro_users_username_key UNIQUE (username);
    END IF;
    
    -- Adiciona password_hash se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='password_hash') THEN
        ALTER TABLE maestro_users ADD COLUMN password_hash TEXT;
        -- Se houver registros sem senha, define um hash inválido
        UPDATE maestro_users SET password_hash = '' WHERE password_hash IS NULL;
        ALTER TABLE maestro_users ALTER COLUMN password_hash SET NOT NULL;
    END IF;
    
    -- Adiciona email se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='email') THEN
        ALTER TABLE maestro_users ADD COLUMN email VARCHAR(255);
    END IF;
    
    -- Adiciona active se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='active') THEN
        ALTER TABLE maestro_users ADD COLUMN active BOOLEAN DEFAULT TRUE;
    END IF;
    
    -- Adiciona created_at se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='created_at') THEN
        ALTER TABLE maestro_users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
    
    -- Adiciona updated_at se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='updated_at') THEN
        ALTER TABLE maestro_users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
    
    -- Adiciona last_login se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='maestro_users' AND column_name='last_login') THEN
        ALTER TABLE maestro_users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Remove constraint UNIQUE se já existir e recria (para evitar erros)
DO $$
BEGIN
    -- Remove constraint de username se existir
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'maestro_users_username_key') THEN
        ALTER TABLE maestro_users DROP CONSTRAINT maestro_users_username_key;
    END IF;
    -- Cria constraint UNIQUE em username
    ALTER TABLE maestro_users ADD CONSTRAINT maestro_users_username_key UNIQUE (username);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Cria índices (se não existirem)
CREATE INDEX IF NOT EXISTS idx_maestro_users_username ON maestro_users(username);
CREATE INDEX IF NOT EXISTS idx_maestro_users_email ON maestro_users(email);
CREATE INDEX IF NOT EXISTS idx_maestro_users_active ON maestro_users(active);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Remove trigger se existir e recria
DROP TRIGGER IF EXISTS update_maestro_users_updated_at ON maestro_users;
CREATE TRIGGER update_maestro_users_updated_at
    BEFORE UPDATE ON maestro_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilita Row Level Security (RLS)
ALTER TABLE maestro_users ENABLE ROW LEVEL SECURITY;

-- Remove políticas antigas se existirem
DROP POLICY IF EXISTS "Service role can access all maestro_users" ON maestro_users;

-- Política para permitir acesso via service role
-- (A aplicação usa service role key, então pode acessar diretamente)
CREATE POLICY "Service role can access all maestro_users"
    ON maestro_users
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Comentários na tabela
COMMENT ON TABLE maestro_users IS 'Tabela de usuários do sistema Maestro';
COMMENT ON COLUMN maestro_users.username IS 'Nome de usuário único';
COMMENT ON COLUMN maestro_users.password_hash IS 'Hash bcrypt da senha';
COMMENT ON COLUMN maestro_users.email IS 'Email do usuário (opcional)';
COMMENT ON COLUMN maestro_users.active IS 'Indica se o usuário está ativo';
COMMENT ON COLUMN maestro_users.last_login IS 'Data e hora do último login';

-- Verifica se a tabela foi criada corretamente
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'maestro_users') THEN
        RAISE NOTICE 'Tabela maestro_users criada/atualizada com sucesso!';
    ELSE
        RAISE EXCEPTION 'Erro: Tabela maestro_users não foi criada';
    END IF;
END $$;
