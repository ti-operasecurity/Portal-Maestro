-- Script SQL SIMPLIFICADO para criar a tabela de usuários no Supabase
-- Use este script se o anterior der erro
-- Execute no SQL Editor do Supabase
-- Nome da tabela: maestro_users

-- Remove a tabela se já existir (CUIDADO: apaga todos os dados!)
DROP TABLE IF EXISTS maestro_users CASCADE;

-- Cria a tabela de usuários
CREATE TABLE maestro_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Cria índices
CREATE INDEX idx_maestro_users_username ON maestro_users(username);
CREATE INDEX idx_maestro_users_email ON maestro_users(email);

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para updated_at
CREATE TRIGGER update_maestro_users_updated_at
    BEFORE UPDATE ON maestro_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilita RLS
ALTER TABLE maestro_users ENABLE ROW LEVEL SECURITY;

-- Política para service role
CREATE POLICY "Service role can access all maestro_users"
    ON maestro_users
    FOR ALL
    USING (true)
    WITH CHECK (true);
