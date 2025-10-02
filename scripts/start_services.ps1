param(
    [switch]$NoRedis,
    [switch]$NoBeat,
    [switch]$NoWorker,
    [switch]$NoServer,
    [string]$WslDistro = "Ubuntu",
    [int]$PortTimeoutSec = 30,
    [string]$VenvActivatePath,
    [switch]$Migrate,
    [switch]$RunImport,
    [int]$ImportLimit,
    [string]$ImportSinceDate,
    [switch]$ImportDryRun,
    [switch]$OpenBrowser,
    [string]$ServerBind = "127.0.0.1",
    [int]$ServerPort = 8000,
    [switch]$AutoPort
)

# Force UTF-8 in the current session (fix console mojibake and ensure Python UTF-8 IO)
try { chcp 65001 > $null } catch { }
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PGCLIENTENCODING = 'UTF8'

# Utility: write info
function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }

# Utility: test if a TCP port is free on localhost
function Test-PortFree {
    param(
        [int]$Port
    )
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}
function Write-Warn($msg) { Write-Warning $msg }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Utility: wait for TCP port to open
function Wait-Port {
    param(
        [string]$TargetHost,
        [int]$Port,
        [int]$TimeoutSec = 30
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $iar = $client.BeginConnect($TargetHost, $Port, $null, $null)
            $ok = $iar.AsyncWaitHandle.WaitOne(1000, $false)
            if ($ok -and $client.Connected) {
                $client.EndConnect($iar)
                $client.Close()
                return $true
            }
            $client.Close()
        } catch { }
    }
    return $false
}

# Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir   # assumes scripts/ under project root
# Try to locate venv in project root or repository root (parent of project)
$RepoDir = Split-Path -Parent $ProjectDir
$VenvCandidates = @(
    (Join-Path $ProjectDir "venv\Scripts\Activate.ps1"),
    (Join-Path $RepoDir "venv\Scripts\Activate.ps1")
)
$VenvActivate = $null
if ($VenvActivatePath) {
    if (Test-Path $VenvActivatePath) {
        $VenvActivate = $VenvActivatePath
        Write-Info "Venv personnalisé détecté: $VenvActivate"
    } else {
        Write-Warn "Chemin venv fourni introuvable: $VenvActivatePath"
    }
}
if (-not $VenvActivate) {
    foreach ($cand in $VenvCandidates) {
        if (Test-Path $cand) { $VenvActivate = $cand; break }
    }
}

if (-not $VenvActivate) {
    Write-Warn "Environnement virtuel non trouvé dans: $($VenvCandidates -join ', ')"
    Write-Warn "Activez votre venv manuellement ou utilisez -VenvActivatePath pour préciser le chemin."
} else {
    Write-Info "Venv utilisé: $VenvActivate"
}

# 1) Start Redis via Docker (preferred on Windows)
if (-not $NoRedis) {
    Write-Info "Vérification de Docker pour Redis"
    $dockerOk = $true
    try { docker --version | Out-Null } catch { $dockerOk = $false }
    if (-not $dockerOk) {
        Write-Err "Docker n'est pas disponible. Installez Docker Desktop ou lancez Redis manuellement."
    } else {
        # Vérifier si un conteneur nommé 'redis' existe déjà
        $existing = (docker ps -a --filter "name=^/redis$" --format "{{.ID}}")
        if (-not $existing) {
            Write-Info "Création du conteneur Redis (redis:7-alpine) sur le port 6379"
            docker run -d --name redis -p 6379:6379 redis:7-alpine | Out-Null
        } else {
            # Démarrer si pas en cours d'exécution
            $running = (docker ps --filter "name=^/redis$" --format "{{.ID}}")
            if (-not $running) {
                Write-Info "Démarrage du conteneur Redis existant"
                docker start redis | Out-Null
            } else {
                Write-Info "Conteneur Redis déjà en cours d'exécution"
            }
        }

        Write-Info "Attente d'ouverture du port 6379 (Docker -> Windows)"
        if (-not (Wait-Port -TargetHost "127.0.0.1" -Port 6379 -TimeoutSec $PortTimeoutSec)) {
            Write-Warn "Le port 6379 n'est pas accessible. Vérifiez Docker/Redis et le pare-feu."
        } else {
            Write-Info "Redis accessible sur 127.0.0.1:6379"
            # Health check via Python redis ping using URLs from .env if available
            $envPath = Join-Path $ProjectDir ".env"
            $RedisUrl = $null
            $RedisCacheUrl = $null
            if (Test-Path $envPath) {
                $lines = Get-Content -Path $envPath -ErrorAction SilentlyContinue
                foreach ($l in $lines) {
                    if ($l -match '^\s*REDIS_URL\s*=\s*(.+)') { $RedisUrl = $Matches[1].Trim() }
                    if ($l -match '^\s*REDIS_CACHE_URL\s*=\s*(.+)') { $RedisCacheUrl = $Matches[1].Trim() }
                }
            }
            if (-not $RedisUrl) { $RedisUrl = "redis://127.0.0.1:6379/0" }
            if (-not $RedisCacheUrl) { $RedisCacheUrl = "redis://127.0.0.1:6379/1" }

            function Invoke-RedisPing([string]$url) {
                $py = @"
import os
import sys
import redis
url = sys.argv[1]
try:
    r = redis.from_url(url)
    r.ping()
    print('OK')
    sys.exit(0)
except Exception as e:
    print('ERR:', e)
    sys.exit(1)
"@
                $tempPy = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".py")
                Set-Content -Path $tempPy -Value $py -Encoding UTF8
                $outFile = [System.IO.Path]::GetTempFileName()
                $errFile = [System.IO.Path]::GetTempFileName()

                $proc = Start-Process -FilePath "python" -ArgumentList @($tempPy, $url) -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
                $proc.WaitForExit()

                $out = ""
                $err = ""
                if (Test-Path $outFile) { $out = Get-Content $outFile -Raw }
                if (Test-Path $errFile) { $err = Get-Content $errFile -Raw }

                Remove-Item $tempPy, $outFile, $errFile -ErrorAction SilentlyContinue

                return @{ Code = $proc.ExitCode; Out = $out; Err = $err }
            }

            foreach ($target in @($RedisUrl, $RedisCacheUrl)) {
                $ok = $false
                for ($i=0; $i -lt 5; $i++) {
                    $res = Invoke-RedisPing -url $target
                    if ($res.Code -eq 0) { $ok = $true; break }
                    Start-Sleep -Seconds 1
                }
                if ($ok) {
                    Write-Info "Redis ping OK: $target"
                } else {
                    Write-Warn "Redis ping ÉCHEC: $target. Sortie: $($res.Out) $($res.Err)"
                }
            }
        }
    }
}
# Helper to start a new PowerShell window with venv activated
function Start-Window {
    param(
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command
    )
    $psCmd = @()
    $psCmd += "Set-Location `"$WorkingDir`";"
    # Force UTF-8 in each child window to avoid encoding errors (escape $ to prevent parent interpolation)
    $psCmd += 'chcp 65001 > $null; $env:PYTHONUTF8=1;'
    if (Test-Path $VenvActivate) { $psCmd += ". `"$VenvActivate`";" }
    $psCmd += $Command
    $joined = $psCmd -join ' '
    $argList = @('-NoExit', '-Command', $joined)

    Start-Process -FilePath "powershell" -ArgumentList $argList -WorkingDirectory $WorkingDir | Out-Null
    Write-Info "Lancé: $Title"
}

# 2) Django runserver
if (-not $NoServer) {
    $finalPort = $ServerPort
    if ($AutoPort) {
        for ($p = $ServerPort; $p -lt ($ServerPort + 20); $p++) {
            if (Test-PortFree -Port $p) { $finalPort = $p; break }
        }
        if ($finalPort -ne $ServerPort) {
            Write-Info "Port libre trouvé: $finalPort (au lieu de $ServerPort)"
        } else {
            Write-Warn "Aucun port libre trouvé entre $ServerPort et $($ServerPort+19). Tentative sur $ServerPort."
        }
    }
    # Ensure ML init is enabled only for server process (can be disabled during migrations below)
    # Escape $ so that the env var is set in the child session, not expanded in the parent
    $serverCmd = "`$env:RECO_INIT_MODELS_ON_STARTUP='1'; python manage.py runserver ${ServerBind}:$finalPort"
    Start-Window -Title "Django Server (${ServerBind}:$finalPort)" -WorkingDir $ProjectDir -Command $serverCmd
    if ($OpenBrowser) {
        Start-Sleep -Seconds 2
        # Avoid PowerShell parsing $ServerBind: as a scoped variable by using -f formatting
        $url = "http://{0}:{1}/" -f $ServerBind, $finalPort
        Start-Process $url
    }
}

# 3) Celery worker
if (-not $NoWorker) {
    Start-Window -Title "Celery Worker" -WorkingDir $ProjectDir -Command "celery -A config.celery:app worker -l info -P solo"
}

# 4) Celery beat
if (-not $NoBeat) {
    Start-Window -Title "Celery Beat" -WorkingDir $ProjectDir -Command "celery -A config.celery:app beat -l info"
}

Write-Info "Tous les services demandés ont été lancés (fenêtres séparées)."
Write-Info "Astuce: utilisez -NoRedis / -NoBeat / -NoWorker / -NoServer pour désactiver certains services."

# 5) Optional: run migrations and DGCCRF import in current shell (blocking)
if ($Migrate) {
    Write-Info "Application des migrations (init ML désactivée pendant l'opération)"
    $prev = $env:RECO_INIT_MODELS_ON_STARTUP
    $env:RECO_INIT_MODELS_ON_STARTUP = '0'
    try {
        python manage.py makemigrations
        python manage.py migrate
        Write-Info "Migrations terminées"
    } catch {
        Write-Err "Echec migrations: $($_.Exception.Message)"
    } finally {
        if ($null -ne $prev) { $env:RECO_INIT_MODELS_ON_STARTUP = $prev } else { Remove-Item Env:RECO_INIT_MODELS_ON_STARTUP -ErrorAction SilentlyContinue }
    }
}

if ($RunImport) {
    Write-Info "Import DGCCRF (import_dgccrf)"
    $importParams = @('import_dgccrf')
    if ($ImportDryRun) { $importParams += '--dry-run' }
    if ($ImportLimit) { $importParams += @('--limit', $ImportLimit) }
    if ($ImportSinceDate) { $importParams += @('--since', $ImportSinceDate) }
    try {
        python manage.py $importParams
        Write-Info "Import DGCCRF terminé"
    } catch {
        Write-Err "Echec import DGCCRF: $($_.Exception.Message)"
    }
}
