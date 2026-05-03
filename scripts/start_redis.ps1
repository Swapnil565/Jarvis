# Start Redis via Docker Compose (Windows PowerShell)
# Usage: ./scripts/start_redis.ps1

$composeFile = "${PSScriptRoot}/../docker-compose.redis.yml"
if (-not (Test-Path $composeFile)) {
    Write-Error "docker-compose file not found: $composeFile"
    exit 1
}

Write-Host "Starting Redis using docker-compose file: $composeFile"
docker compose -f $composeFile up -d

# Wait and verify
Start-Sleep -Seconds 2
$container = docker ps --filter "name=jarvis-redis" --format "{{.Names}}"
if ($container -eq "jarvis-redis") {
    Write-Host "Redis container 'jarvis-redis' is running"
} else {
    Write-Host "Redis container not found in docker ps; check 'docker compose logs' for errors"
}

Write-Host "To stop: docker compose -f $composeFile down"