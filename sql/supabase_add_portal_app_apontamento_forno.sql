-- Adiciona aplicação "Apontamento Forno" na aba Aplicações

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
    'apontamento-forno',
    'Apontamento Forno',
    'Sistema de Apontamento de caixas do Forno',
    '/proxy/apontamento-forno',
    TRUE
)
ON CONFLICT (key) DO NOTHING;

