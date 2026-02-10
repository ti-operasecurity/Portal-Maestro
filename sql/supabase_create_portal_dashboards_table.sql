-- Tabela separada para Dashboards (aba Dashboards), mantendo maestro_portal_applications só para a aba Aplicações.

-- 1) Criar tabela maestro_portal_dashboards (mesmo padrão: key, name, description, url, active)
CREATE TABLE IF NOT EXISTS maestro_portal_dashboards (
    id BIGSERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- 2) Inserir dashboards (Inspeção Final x Estoque + Ocupação do dia Forno movido da aba Aplicações)
INSERT INTO maestro_portal_dashboards (key, name, description, url, active)
VALUES
    ('inspecao-final-estoque', 'Inspeção Final x Estoque', 'Peças aprovadas IF x Entrada estoque', '/proxy/inspecao-final-estoque', TRUE),
    ('dashboard-ocupacao-hoje', 'Ocupação do dia Forno', 'Peças distribuidas por Fornos', '/proxy/dashboard-ocupacao-hoje', TRUE)
ON CONFLICT (key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    active = EXCLUDED.active;

-- 3) Remover da aba Aplicações os itens que foram para Dashboards (e permissões de usuário associadas)
DELETE FROM maestro_user_portal_app_access
WHERE portal_app_id IN (
    SELECT id FROM maestro_portal_applications
    WHERE key IN ('inspecao-final-estoque', 'dashboard-ocupacao-hoje')
);

DELETE FROM maestro_portal_applications
WHERE key IN ('inspecao-final-estoque', 'dashboard-ocupacao-hoje');

-- 4) Opcional: remover coluna tab_key de maestro_portal_applications (não usada mais)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'maestro_portal_applications' AND column_name = 'tab_key'
    ) THEN
        ALTER TABLE maestro_portal_applications DROP COLUMN tab_key;
    END IF;
END $$;
