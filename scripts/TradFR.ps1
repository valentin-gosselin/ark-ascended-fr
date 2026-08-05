# TradFR — installation et mise à jour du patch de traduction FR pour ARK: Survival Ascended
# Usage : double-cliquer installer.bat, ou : powershell -File TradFR.ps1 [-Auto]
param([switch]$Auto)

$Repo = "valentin-gosselin/ark-ascended-fr"
$Pak  = "TradFR_P.pak"

function Trouver-Paks {
    # 1. chemin Steam dans le registre, puis parcours des bibliothèques
    try {
        $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction Stop).SteamPath
        $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
        $libs = @($steam)
        if (Test-Path $vdf) {
            $libs += (Select-String '"path"\s+"([^"]+)"' $vdf -AllMatches).Matches |
                     ForEach-Object { $_.Groups[1].Value -replace '\\\\', '\' }
        }
        foreach ($lib in $libs | Select-Object -Unique) {
            $p = Join-Path $lib "steamapps\common\ARK Survival Ascended\ShooterGame\Content\Paks"
            if (Test-Path $p) { return $p }
        }
    } catch {}
    # 2. demande manuelle
    if ($Auto) { throw "Dossier Paks introuvable" }
    Read-Host "Dossier Paks introuvable. Collez le chemin ...\ShooterGame\Content\Paks"
}

$paks = Trouver-Paks
$cible = Join-Path $paks $Pak
$verFile = "$cible.version"

# version distante (dernière release GitHub)
$rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "TradFR" }
$distante = $rel.tag_name
$locale = if (Test-Path $verFile) { Get-Content $verFile } else { "(absente)" }

if ($locale -eq $distante -and (Test-Path $cible)) {
    Write-Host "TradFR déjà à jour ($locale)."
    exit 0
}
if (Get-Process ArkAscended -ErrorAction SilentlyContinue) {
    Write-Host "ARK est en cours d'exécution : fermez le jeu puis relancez la mise à jour."
    exit 1
}

$asset = $rel.assets | Where-Object name -eq $Pak
Write-Host "Téléchargement de TradFR $distante..."
Invoke-WebRequest $asset.browser_download_url -OutFile $cible
Set-Content $verFile $distante
Write-Host "Installé : $cible ($locale -> $distante)"

# proposition de mise à jour automatique (tâche à l'ouverture de session)
if (-not $Auto) {
    $r = Read-Host "Activer la mise à jour automatique à chaque ouverture de session ? [o/N]"
    if ($r -match '^[oOyY]') {
        $moi = $MyInvocation.MyCommand.Path
        $dest = Join-Path $env:LOCALAPPDATA "TradFR\TradFR.ps1"
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        Copy-Item $moi $dest -Force
        schtasks /create /f /tn "TradFR MAJ" /sc onlogon /rl limited `
            /tr "powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \`"$dest\`" -Auto" | Out-Null
        Write-Host "Mise à jour automatique activée (tâche planifiée « TradFR MAJ »)."
        Write-Host "Pour la retirer : schtasks /delete /tn `"TradFR MAJ`" /f"
    }
}
