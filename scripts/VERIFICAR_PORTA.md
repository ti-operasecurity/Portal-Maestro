# Como Verificar Qual Processo Está Usando a Porta 80

## Linux (CentOS/Ubuntu/Debian)

### Método 1: Usando `netstat`
```bash
# Ver processo usando porta 80
sudo netstat -tulpn | grep :80

# Ou mais específico
sudo netstat -tulpn | grep :80 | grep LISTEN
```

### Método 2: Usando `ss` (mais moderno)
```bash
# Ver processo usando porta 80
sudo ss -tulpn | grep :80

# Ou mais específico
sudo ss -tulpn | grep :80 | grep LISTEN
```

### Método 3: Usando `lsof`
```bash
# Ver processo usando porta 80
sudo lsof -i :80

# Ou mais detalhado
sudo lsof -i :80 -P -n
```

### Método 4: Usando `fuser`
```bash
# Ver qual processo está usando a porta 80
sudo fuser 80/tcp

# Ver detalhes do processo
sudo fuser -v 80/tcp
```

### Método 5: Usando `systemctl` (se for serviço systemd)
```bash
# Verificar se Apache está rodando
sudo systemctl status httpd
# ou
sudo systemctl status apache2

# Verificar se Nginx está rodando
sudo systemctl status nginx
```

## Windows (PowerShell)

### Método 1: Usando `netstat`
```powershell
# Ver processo usando porta 80
netstat -ano | findstr :80

# Ver apenas conexões LISTENING
netstat -ano | findstr :80 | findstr LISTENING
```

### Método 2: Usando `Get-NetTCPConnection` (PowerShell)
```powershell
# Ver processo usando porta 80
Get-NetTCPConnection -LocalPort 80 | Select-Object LocalAddress, LocalPort, State, OwningProcess

# Ver detalhes do processo
Get-NetTCPConnection -LocalPort 80 | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        Port = $_.LocalPort
        State = $_.State
        ProcessId = $_.OwningProcess
        ProcessName = $proc.Name
        ProcessPath = $proc.Path
    }
}
```

### Método 3: Usando `Get-Process` com `netstat`
```powershell
# Ver processo e nome
$connections = netstat -ano | findstr :80
foreach ($conn in $connections) {
    if ($conn -match '\s+(\d+)$') {
        $pid = $matches[1]
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        Write-Host "PID: $pid | Processo: $($proc.Name) | Caminho: $($proc.Path)"
    }
}
```

## Exemplos de Saída

### Linux (netstat)
```
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      1234/nginx
```
- `1234` = PID do processo
- `nginx` = Nome do processo

### Linux (ss)
```
tcp   LISTEN 0      128          0.0.0.0:80        0.0.0.0:*    users:(("nginx",pid=1234,fd=6))
```

### Windows (netstat)
```
TCP    0.0.0.0:80             0.0.0.0:0              LISTENING       1234
```
- `1234` = PID do processo

## Como Matar o Processo (se necessário)

### Linux
```bash
# Matar processo por PID
sudo kill 1234

# Matar processo forçadamente
sudo kill -9 1234

# Matar processo por nome
sudo pkill nginx
# ou
sudo killall nginx
```

### Windows
```powershell
# Matar processo por PID
Stop-Process -Id 1234 -Force

# Matar processo por nome
Stop-Process -Name "nginx" -Force
```

## Verificar se a Porta 80 Está Livre

### Linux
```bash
# Verificar se porta 80 está em uso
if sudo netstat -tuln | grep -q ":80 "; then
    echo "Porta 80 está em uso"
else
    echo "Porta 80 está livre"
fi
```

### Windows (PowerShell)
```powershell
# Verificar se porta 80 está em uso
$port = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port) {
    Write-Host "Porta 80 está em uso"
} else {
    Write-Host "Porta 80 está livre"
}
```

## Processos Comuns que Usam Porta 80

- **Apache (httpd)**: Servidor web Apache
- **Nginx**: Servidor web Nginx
- **IIS**: Internet Information Services (Windows)
- **Outros containers Docker**: Outros containers podem estar usando a porta
- **Outras aplicações Flask/Django**: Outras aplicações Python

## Soluções Comuns

### Se Apache estiver usando a porta 80:
```bash
# Parar Apache
sudo systemctl stop httpd
# ou
sudo systemctl stop apache2

# Desabilitar Apache para não iniciar no boot
sudo systemctl disable httpd
```

### Se Nginx estiver usando a porta 80:
```bash
# Parar Nginx
sudo systemctl stop nginx

# Desabilitar Nginx para não iniciar no boot
sudo systemctl disable nginx
```

### Se outro container Docker estiver usando:
```bash
# Ver containers rodando
docker ps

# Parar container específico
docker stop nome-do-container

# Ver qual container está usando a porta
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep :80
```

## Script de Verificação Completa (Linux)

Crie um arquivo `check_port_80.sh`:

```bash
#!/bin/bash

echo "=== Verificando Porta 80 ==="
echo ""

# Verificar com netstat
echo "1. Verificação com netstat:"
if sudo netstat -tulpn | grep -q ":80 "; then
    sudo netstat -tulpn | grep :80
else
    echo "   Porta 80 não está em uso (netstat)"
fi

echo ""

# Verificar com ss
echo "2. Verificação com ss:"
if sudo ss -tulpn | grep -q ":80 "; then
    sudo ss -tulpn | grep :80
else
    echo "   Porta 80 não está em uso (ss)"
fi

echo ""

# Verificar serviços comuns
echo "3. Verificando serviços comuns:"
if systemctl is-active --quiet httpd 2>/dev/null; then
    echo "   Apache (httpd) está rodando"
fi
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo "   Apache (apache2) está rodando"
fi
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "   Nginx está rodando"
fi

echo ""

# Verificar containers Docker
echo "4. Verificando containers Docker:"
if command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(NAMES|:80)"
else
    echo "   Docker não está instalado"
fi
```

Torne executável:
```bash
chmod +x check_port_80.sh
./check_port_80.sh
```

