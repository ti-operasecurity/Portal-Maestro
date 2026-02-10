-- Migration: adiciona coluna de URL (se não existir) e insere primeira aplicação da aba Aplicações

-- 1) Garantir coluna URL na tabela de aplicações do portal
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'maestro_portal_applications' AND column_name = 'url'
    ) THEN
        ALTER TABLE maestro_portal_applications ADD COLUMN url TEXT;
    END IF;
END $$;

-- 2) Inserir aplicação inicial (porta 8090)
INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'app-8090',
    'Vinculação de ProductionOrders | SAP',
    NULL,
    '/proxy/app-8090',
    TRUE
)
ON CONFLICT (key) DO NOTHING;

