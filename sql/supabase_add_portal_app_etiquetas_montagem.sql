-- Adiciona aplicação "Etiquetas Montagem" na aba Aplicações

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

-- Inserir aplicação "Etiquetas Montagem"
INSERT INTO maestro_portal_applications (key, name, description, url, active)
VALUES (
    'etiquetas-montagem',
    'Etiquetas Montagem',
    'Aplicação de geração de Seriais',
    '/proxy/etiquetas-montagem',
    TRUE
)
ON CONFLICT (key) DO UPDATE
SET 
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    active = EXCLUDED.active;

