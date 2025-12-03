#!/bin/bash

# Script para verificar variáveis de ambiente no container

CONTAINER_NAME="maestro-portal"

echo "Verificando variáveis de ambiente no container..."
echo ""

docker exec "$CONTAINER_NAME" env | grep -E "SUPABASE|SECRET" | while IFS= read -r line; do
    var_name=$(echo "$line" | cut -d '=' -f 1)
    var_value=$(echo "$line" | cut -d '=' -f 2-)
    # Mostra apenas os primeiros 50 caracteres do valor para não expor tudo
    value_preview="${var_value:0:50}..."
    echo "$var_name=${value_preview}"
    # Verifica se há \r
    if echo "$var_value" | grep -q $'\r'; then
        echo "  ⚠️  CONTÉM \\r (carriage return)!"
    fi
done

echo ""
echo "Testando conexão com Supabase..."
docker exec "$CONTAINER_NAME" python -c "
import os
url = os.getenv('SUPABASE_URL', '')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
print(f'URL length: {len(url)}')
print(f'Key length: {len(key)}')
print(f'URL has \\r: {\"\\r\" in url}')
print(f'Key has \\r: {\"\\r\" in key}')
if url:
    print(f'URL first 50 chars: {url[:50]}')
"

