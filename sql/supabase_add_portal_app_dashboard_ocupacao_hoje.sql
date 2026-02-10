-- Adiciona aplicação "Ocupação do dia Forno" na aba Aplicações

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
    'dashboard-ocupacao-hoje',
    'Ocupação do dia Forno',
    'Peças distribuidas por Fornos',
    '/proxy/dashboard-ocupacao-hoje',
    TRUE
)
ON CONFLICT (key) DO NOTHING;
