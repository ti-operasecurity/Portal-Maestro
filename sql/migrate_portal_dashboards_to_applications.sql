-- Migração: mover dados de maestro_portal_dashboards para maestro_applications
-- e deixar de usar a tabela maestro_portal_dashboards.
--
-- 1) Adicionar coluna section em maestro_applications (se não existir)
--    Valores: 'main' = aplicação principal; 'portal_dashboard' = item da antiga aba Dashboards.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'maestro_applications' AND column_name = 'section'
    ) THEN
        ALTER TABLE maestro_applications
        ADD COLUMN section TEXT DEFAULT 'main';
    END IF;
END $$;

-- Garantir que registros existentes tenham section = 'main'
UPDATE maestro_applications SET section = 'main' WHERE section IS NULL;

-- 2) Inserir em maestro_applications os registros de maestro_portal_dashboards
--    Mapeamento: key -> url_proxy e name; name -> display_name

INSERT INTO maestro_applications (name, url_proxy, display_name, icon, color, active, section)
SELECT
    d.key,
    d.key,
    d.name,
    'chart-pie',
    '#06b6d4',
    COALESCE(d.active, TRUE),
    'portal_dashboard'
FROM maestro_portal_dashboards d
WHERE NOT EXISTS (SELECT 1 FROM maestro_applications a WHERE a.url_proxy = d.key);

-- Se já existir registro com mesmo url_proxy (ex.: key), marcar como portal_dashboard
UPDATE maestro_applications a
SET section = 'portal_dashboard',
    display_name = d.name,
    active = COALESCE(d.active, TRUE)
FROM maestro_portal_dashboards d
WHERE a.url_proxy = d.key;

-- 3) Opcional: remover a tabela maestro_portal_dashboards (descomente após validar a migração)
-- DROP TABLE IF EXISTS maestro_portal_dashboards;
