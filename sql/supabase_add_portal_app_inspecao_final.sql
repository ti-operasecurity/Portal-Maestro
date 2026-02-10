-- Adiciona a aplicação "Apontamento Inspeção Final" na aba Aplicações (Portal)
-- URL: https://10.150.16.45:9010/
-- Nome: Apontamento Inspeção Final
-- Descrição: Sistema de apontamento de peças Inspeção Final

-- Garantir que a coluna 'url' existe na tabela
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'maestro_portal_applications' 
        AND column_name = 'url'
    ) THEN
        ALTER TABLE maestro_portal_applications ADD COLUMN url TEXT;
    END IF;
END $$;

-- Inserir a nova aplicação
INSERT INTO maestro_portal_applications (key, name, description, url)
VALUES (
    'apontamento-inspecao-final',
    'Apontamento Inspeção Final',
    'Sistema de apontamento de peças Inspeção Final',
    '/proxy/apontamento-inspecao-final'
)
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url;

