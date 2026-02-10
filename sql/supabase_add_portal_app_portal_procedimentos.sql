-- Adiciona aplicação "Portal de Procedimentos" na aba Aplicações

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

INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'portal-procedimentos',
    'Portal de Procedimentos',
    'Procedimentos de autoajuda interno',
    '/proxy/portal-procedimentos',
    TRUE
)
ON CONFLICT (key) DO NOTHING;
