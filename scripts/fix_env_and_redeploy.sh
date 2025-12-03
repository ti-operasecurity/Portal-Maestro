#!/bin/bash

# Script para corrigir .env e fazer redeploy completo

CONTAINER_NAME="maestro-portal"

echo "🔧 Corrigindo arquivo .env..."
echo ""

# Converter quebras de linha
if command -v dos2unix &> /dev/null; then
    dos2unix .env
    echo "✅ Convertido com dos2unix"
else
    sed -i 's/\r$//' .env
    echo "✅ Convertido com sed"
fi

# Remover espaços extras e caracteres de controle
sed -i 's/[[:space:]]*$//' .env
sed -i 's/^[[:space:]]*//' .env

echo ""
echo "📋 Verificando conteúdo do .env (primeiras linhas):"
head -5 .env | while IFS= read -r line; do
    if [[ "$line" =~ ^[^#]*= ]]; then
        var_name=$(echo "$line" | cut -d '=' -f 1)
        var_value=$(echo "$line" | cut -d '=' -f 2- | head -c 30)
        echo "  $var_name=${var_value}..."
    fi
done

echo ""
echo "🛑 Parando e removendo container atual..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
echo "✅ Container removido"

echo ""
echo "🔨 Fazendo deploy completo..."
./deploy-linux.sh --full-deploy

echo ""
echo "✅ Processo concluído!"
echo ""
echo "Agora teste o login com:"
echo "  Usuário: Opera"
echo "  Senha: Opera@2026"

