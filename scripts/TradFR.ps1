# TradFR - installation et mise a jour du patch de traduction FR pour ARK: Survival Ascended
# Compatible Windows PowerShell 5.1 (Windows 10/11 par defaut).
# Usage : double-cliquer installer.bat, ou : powershell -ExecutionPolicy Bypass -File TradFR.ps1 [-Auto]
param([switch]$Auto)

$Repo = "valentin-gosselin/ark-ascended-fr"
$Pak  = "TradFR_P.pak"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"

function Trouver-Paks {
    # chemin Steam dans le registre, puis parcours des bibliotheques
    try {
        $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction Stop).SteamPath
        $steam = $steam -replace "/", "\"
        $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
        $libs = @($steam)
        if (Test-Path $vdf) {
            $m = Select-String '"path"\s+"([^"]+)"' $vdf -AllMatches
            foreach ($x in $m.Matches) { $libs += ($x.Groups[1].Value -replace "\\\\", "\") }
        }
        foreach ($lib in ($libs | Select-Object -Unique)) {
            $p = Join-Path $lib "steamapps\common\ARK Survival Ascended\ShooterGame\Content\Paks"
            if (Test-Path $p) { return $p }
        }
    } catch {}
    if ($Auto) { throw "Dossier Paks introuvable" }
    while ($true) {
        $p = Read-Host "Dossier Paks introuvable. Collez le chemin ...\ShooterGame\Content\Paks"
        $p = $p.Trim().Trim('"')
        if (Test-Path $p) { return $p }
        Write-Host "Ce dossier n'existe pas, reessayez."
    }
}

$paks = Trouver-Paks
$cible = Join-Path $paks $Pak
$verFile = "$cible.version"

# version distante (derniere release GitHub)
$rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "TradFR" }
$distante = $rel.tag_name
$locale = "(absente)"
if (Test-Path $verFile) { $locale = (Get-Content $verFile -First 1).Trim() }

if (($locale -eq $distante) -and (Test-Path $cible)) {
    Write-Host "TradFR deja a jour ($locale)."
} else {
    if (Get-Process ArkAscended -ErrorAction SilentlyContinue) {
        Write-Host "ARK est en cours d'execution : fermez le jeu puis relancez la mise a jour."
        exit 1
    }
    $asset = $rel.assets | Where-Object { $_.name -eq $Pak }
    Write-Host "Telechargement de TradFR $distante..."
    Invoke-WebRequest $asset.browser_download_url -OutFile $cible
    Set-Content -Path $verFile -Value $distante
    Write-Host "Installe : $cible ($locale -> $distante)"
}

# proposition de mise a jour automatique (tache a l'ouverture de session)
if (-not $Auto) {
    $r = Read-Host "Activer la mise a jour automatique a chaque ouverture de session ? [o/N]"
    if ($r -match "^[oOyY]") {
        $dest = Join-Path $env:LOCALAPPDATA "TradFR\TradFR.ps1"
        New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
        Copy-Item $MyInvocation.MyCommand.Path $dest -Force
        $action = New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$dest`" -Auto"
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        Register-ScheduledTask -TaskName "TradFR MAJ" -Action $action -Trigger $trigger -Force | Out-Null
        Write-Host "Mise a jour automatique activee (tache planifiee 'TradFR MAJ')."
        Write-Host "Pour la retirer : Unregister-ScheduledTask -TaskName 'TradFR MAJ'"
    }
}
