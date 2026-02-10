-- Adiciona as aplicações movidas da tela principal para a aba Aplicações
-- Aplicações: Robô Logistica, Monitoramento Autoclaves, Monitoramento de Fornos

-- Garantir coluna URL existe (caso não tenha rodado migração anterior)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'maestro_portal_applications' AND column_name = 'url'
    ) THEN
        ALTER TABLE maestro_portal_applications ADD COLUMN url TEXT;
    END IF;
END $$;

-- Inserir Robô Logistica
INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'robo-logistica',
    'Robô Logistica',
    'Sistema de automação logística',
    '/proxy/robo-logistica',
    TRUE
)
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    active = EXCLUDED.active;

-- Inserir Monitoramento Autoclaves
INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'monitoramento-autoclaves',
    'Monitoramento Autoclaves',
    'Sistema de monitoramento de autoclaves',
    '/proxy/monitoramento-autoclaves',
    TRUE
)
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    active = EXCLUDED.active;

-- Inserir Monitoramento de Fornos
INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'monitoramento-fornos',
    'Monitoramento de Fornos',
    'Sistema de monitoramento de fornos',
    '/proxy/monitoramento-fornos',
    TRUE
)
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    active = EXCLUDED.active;

