[CmdletBinding()]
param(
    [ValidateSet('Menu', 'Start', 'Stop', 'StartDocker', 'StopAll', 'Check', 'UpdateServer', 'UpdateClient', 'UpdateAll', 'Diagnose', 'Logs', 'SendLogs', 'Configure', 'SetBots', 'ImportDb', 'BackupDb', 'RestoreDb', 'ResetWorld', 'RepairDb', 'DbAccess', 'PanelPassword')]
    [string]$Action = 'Menu',
    [string]$Manifest = '',
    [int]$BotCount = -1,
    [string]$ImportSource = '',
    [string]$RestoreSource = '',
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

# The GUI runs this script hidden with its stdout redirected into a file and
# reads that file back as UTF-8. Without this the redirect gets the console's
# OEM code page instead, and every Polish letter this script prints reaches the
# log broken - "Serwer dzia?a w wersji", while the GUI's own lines beside them
# are fine. Both ends speak UTF-8 now.
try {
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Text.UTF8Encoding]::new($false)
}
catch { }

$serverRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$modulePath = Join-Path $serverRoot 'launcher\Metin2Launcher.psm1'
$diagnosticsModulePath = Join-Path $serverRoot 'launcher\Metin2Launcher.Diagnostics.psm1'
$configPath = Join-Path $serverRoot '.m2launcher.json'
$statePath = Join-Path $serverRoot '.m2launcher-state.json'
# Written when new files are already on disk but Docker did not finish building
# them. Until it is gone the installation is not really on the version its
# VERSION file claims, and starting it would run the previous images.
$rebuildMarkerPath = Join-Path $serverRoot '.m2launcher-rebuild-pending'

foreach ($requiredModule in @($modulePath, $diagnosticsModulePath)) {
    if (-not (Test-Path -LiteralPath $requiredModule -PathType Leaf)) {
        throw "Brakuje modułu launchera: $requiredModule"
    }
}
Import-Module $modulePath -Force

# Where the time goes. Every action prints a "[faza]" line with the seconds
# since the action began at each point that can be slow - Docker checks, the
# download, the file swap, the image build, compose up - so a launcher log
# from a player says which of them took the ten minutes instead of "the
# update is slow". The GUI stamps every line with the clock as well; this is
# for the CLI, and for reading a log without doing the subtraction.
$script:phaseWatch = [Diagnostics.Stopwatch]::StartNew()
function Write-Phase {
    param([Parameter(Mandatory = $true)][string]$Name)
    Write-Host ("[faza] {0} (+{1} s od poczatku akcji)" -f $Name, [int]$script:phaseWatch.Elapsed.TotalSeconds) -ForegroundColor DarkCyan
}
Import-Module $diagnosticsModulePath -Force

function Write-Header {
    Clear-Host
    Write-Host '========================================================' -ForegroundColor DarkYellow
    Write-Host '  Metin2 Singleplayer - Launcher i aktualizacje' -ForegroundColor Yellow
    Write-Host '========================================================' -ForegroundColor DarkYellow
    Write-Host ''
}

function Get-Config {
    return Get-M2LauncherConfig -ServerRoot $serverRoot -ConfigPath $configPath
}

function Get-ManifestSource {
    param($Config)
    if ($Manifest) { return $Manifest }
    return [string]$Config.manifestUrl
}

function Test-RebuildPending {
    return (Test-Path -LiteralPath $rebuildMarkerPath -PathType Leaf)
}

function Read-State {
    # An interrupted update leaves the new VERSION file on disk while the running
    # containers are still the old ones. Reporting that version would make the
    # update check answer "already up to date" and never rebuild, which is the
    # state a player cannot get out of on their own.
    if (Test-RebuildPending) {
        return [pscustomobject]@{ schema = 1; server = 'unknown'; client = 'unknown' }
    }
    # The client the full package shipped, until a client update records a
    # newer one: New-M2DeployTree.ps1 puts CLIENT_VERSION beside VERSION.
    $clientMarker = Join-Path $serverRoot 'CLIENT_VERSION'
    $shippedClient = if (Test-Path -LiteralPath $clientMarker -PathType Leaf) {
        (Get-Content -LiteralPath $clientMarker -Raw).Trim()
    }
    else { 'unknown' }
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ((-not [string]$state.client -or [string]$state.client -eq 'unknown') -and $shippedClient -ne 'unknown') {
            $state.client = $shippedClient
        }
        return $state
    }
    $versionFile = Join-Path $serverRoot 'VERSION'
    $serverVersion = if (Test-Path -LiteralPath $versionFile) {
        (Get-Content -LiteralPath $versionFile -Raw).Trim()
    }
    else { 'unknown' }
    return [pscustomobject]@{ schema = 1; server = $serverVersion; client = $shippedClient }
}

function Save-State {
    param([string]$ServerVersion, [string]$ClientVersion)
    $state = Read-State
    if ($ServerVersion) { $state.server = $ServerVersion }
    if ($ClientVersion) { $state.client = $ClientVersion }
    $state | Select-Object schema, server, client | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Get-ManifestComponent {
    param(
        [Parameter(Mandatory = $true)]$RemoteManifest,
        [Parameter(Mandatory = $true)][ValidateSet('server', 'client')][string]$Name
    )
    $property = $RemoteManifest.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) { return $null }
    $component = $property.Value
    if (-not [string]$component.version -or -not [string]$component.url -or -not [string]$component.sha256) {
        return $null
    }
    return $component
}

function Test-InstalledVersion {
    param(
        [AllowEmptyString()][string]$Installed,
        [AllowEmptyString()][string]$Available
    )
    if (-not $Installed -or -not $Available -or $Installed -eq 'unknown') { return $false }
    return $Installed.Trim().Equals($Available.Trim(), [StringComparison]::OrdinalIgnoreCase)
}

function Confirm-Operation {
    param([Parameter(Mandatory = $true)][string]$Question)
    if ($Yes) { return $true }
    $answer = Read-Host "$Question [t/N]"
    return $answer -match '^(t|tak|y|yes)$'
}

function Show-DockerDiagnostics {
    param([switch]$CheckPanelPort)

    $report = Get-M2DockerPreflight -ServerRoot $serverRoot -CheckPanelPort:$CheckPanelPort
    $text = Format-M2DockerPreflightReport -Report $report
    Write-Host $text -ForegroundColor $(if ($report.CanStart) { 'Green' } else { 'Yellow' })
    return $report
}

function Assert-DockerPrerequisites {
    param([switch]$CheckPanelPort)

    $report = Show-DockerDiagnostics -CheckPanelPort:$CheckPanelPort
    if (-not $report.CanStart) {
        throw (@($report.BlockingIssues) -join [Environment]::NewLine)
    }
}

function Start-Server {
    Assert-DockerPrerequisites -CheckPanelPort
    Write-Phase 'Docker sprawdzony'
    # start-server.ps1 brings the stack up from the images that already exist.
    # After an interrupted update those are the old ones, so finish the build
    # first - otherwise the player keeps running the previous server and the
    # website keeps showing the previous panel.
    if (Test-RebuildPending) {
        Write-Host 'Poprzednia aktualizacja nie dokonczyla budowania. Dokancczam je teraz...' -ForegroundColor Yellow
        Rebuild-Server
        Write-Host 'Budowanie zakonczone.' -ForegroundColor Green
    }
    $script = Join-Path $serverRoot 'start-server.ps1'
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'Brakuje start-server.ps1.' }
    & $script
    if ($LASTEXITCODE -ne 0) { throw "Uruchamianie serwera zakończyło się kodem $LASTEXITCODE." }
    Write-Phase 'Serwer uruchomiony'
}

function Stop-Server {
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'SilentlyContinue'
        docker info 1>$null 2>$null
        $dockerAvailable = $LASTEXITCODE -eq 0
    }
    finally { $ErrorActionPreference = $previousPreference }
    if (-not $dockerAvailable) {
        Write-Host 'Docker jest już zatrzymany.' -ForegroundColor Yellow
        return
    }
    $composeDir = Join-Path $serverRoot 'linux-port\docker'
    $composeFile = Join-Path $composeDir 'docker-compose.yml'
    # `docker compose' writes progress to stderr; under $ErrorActionPreference=
    # 'Stop' Windows PowerShell 5.1 turns that into a terminating error and the
    # stop reports failure even when it worked. Decide from the exit code.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        docker compose --project-directory $composeDir -f $composeFile stop
        $stopExit = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $previousPreference }
    if ($stopExit -ne 0) { throw "Zatrzymywanie serwera zakończyło się kodem $stopExit." }
}

function Start-Docker {
    Assert-DockerPrerequisites
    $script = Join-Path $serverRoot 'start-server.ps1'
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'Brakuje start-server.ps1.' }
    & $script -DockerOnly
    if ($LASTEXITCODE -ne 0) { throw "Uruchamianie Docker Desktop zakończyło się kodem $LASTEXITCODE." }
}

function Stop-DockerAndServer {
    Stop-Server
    $dockerCli = Join-Path $env:ProgramFiles 'Docker\Docker\DockerCli.exe'
    if (Test-Path -LiteralPath $dockerCli -PathType Leaf) {
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'SilentlyContinue'
            & $dockerCli -Shutdown 1>$null 2>$null
        }
        finally { $ErrorActionPreference = $previousPreference }
    }
    else {
        Get-Process -Name 'Docker Desktop', 'com.docker.backend' -ErrorAction SilentlyContinue |
            Stop-Process -ErrorAction SilentlyContinue
    }
    Write-Host 'Serwer i Docker Desktop zatrzymane. Dane pozostają zapisane w wolumenach.' -ForegroundColor Green
}

function Rebuild-Server {
    $composeDir = Join-Path $serverRoot 'linux-port\docker'
    $composeFile = Join-Path $composeDir 'docker-compose.yml'
    # Stopping the server also stops Docker Desktop (see Stop-DockerAndServer),
    # so the sensible order - stop the server, then update it - always arrived
    # here with a dead engine and failed on a raw npipe error, after the files
    # had already been swapped. Start-Server has the same hole: it finishes a
    # pending build before start-server.ps1 gets a chance to bring the engine
    # up, so "click GRAJ" only ever worked when Docker happened to be running.
    # Both paths go through here, so the engine is ensured here as well.
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany - uruchamiam go przed budowaniem.' -ForegroundColor Yellow
        Start-Docker
    }
    # Compose needs the .env before it can build anything - the database
    # passwords are required variables. A copy unpacked by hand has no .env
    # until start-server.ps1 writes one, and that used to run only after this
    # build, so the update failed and "click GRAJ" failed the same way.
    $identityScript = Join-Path $serverRoot 'start-server.ps1'
    if (Test-Path -LiteralPath $identityScript -PathType Leaf) {
        & $identityScript -IdentityOnly
        if ($LASTEXITCODE -ne 0) { throw "Przygotowanie pliku .env zakonczylo sie kodem $LASTEXITCODE." }
    }
    # The overlay is the source of truth; the build context is only a copy of
    # it. Refresh the copy before Docker reads it, or an update that added a
    # source file compiles against the previous one - or, as in 1.23.2, against
    # a header that is not there at all.
    $synced = Sync-M2PlayerbotOverlay -ServerRoot $serverRoot
    if ($synced -gt 0) {
        Write-Host "Zsynchronizowano $synced plik(ow) zrodlowych bota do kontekstu budowania." -ForegroundColor DarkGray
    }
    Write-Phase 'Kontekst budowania przygotowany (.env, nakladka)'
    # The engine patches are part of the overlay too, and until now nothing on a
    # player's machine ever applied them.
    $patched = Invoke-M2EnginePatches -ServerRoot $serverRoot
    if ($patched -gt 0) {
        Write-Host "Nalozono $patched latek silnika." -ForegroundColor DarkGray
    }
    # And the sources the image is actually built from.
    #
    # This check exists in start-server.ps1 too, and that was not enough: this
    # path calls start-server.ps1 with -IdentityOnly, which returns after
    # writing the .env and never reaches it, then builds here. So a player
    # clicking GRAJ went straight to `docker compose --build' with an
    # incomplete context and got fifteen "failed to calculate checksum ... not
    # found" lines. Reported from the Discord twice, the second time against a
    # version that was supposed to have fixed it - because the fix was in the
    # half of the code that click does not run.
    #
    # linux-port/docker/game/src holds the r40250 tree, put there once by
    # fetch-sources.sh during installation. It is the operator's own package and
    # never travels in an update; what an update does put there is
    # src/server/game, because that is where the bot sources belong - which is
    # why a broken install still shows a plausible src/server/game and a build
    # context of about 1.6 MB where a complete one is hundreds of megabytes.
    $gameContext = Join-Path $serverRoot 'linux-port\docker\game\src'
    $requiredContext = @(Get-M2RequiredGameContext -ServerRoot $serverRoot)
    $missingContext = @()
    foreach ($entry in $requiredContext) {
        if (-not (Test-Path -LiteralPath (Join-Path $gameContext $entry))) {
            $missingContext += $entry
        }
    }
    # The dumps, the same way (see start-server.ps1 for why an initialised
    # database is exempt): this is the half of the code that click runs.
    $missingDumps = @(Get-M2MissingSqlDumps -ServerRoot $serverRoot)
    if ($missingDumps.Count -gt 0) {
        $dbVolume = Get-CurrentInstallTargetVolume
        $dbReady = $false
        if ($dbVolume) { $dbReady = Test-M2VolumeInitialized -Volume $dbVolume }
        if (-not $dbReady) {
            throw ("Brakuje zrzutow bazy danych, wiec pierwsza baza powstalaby pusta.`n`n" +
                   "Katalog: " + (Join-Path $serverRoot 'linux-port\docker\mariadb\initdb.d\dumps') + "`n" +
                   "Brakuje: " + ($missingDumps -join ', ') + "`n`n" +
                   "MariaDB wystartowalaby bez schematu gry (i zglosila 'healthy'), a playerbot-migrate " +
                   "czekalby 30 minut na tabele, ktore nigdy nie powstana. Zrzuty pochodza z Twojej " +
                   "paczki serwera r40250 (Server\metin2_mysql_dump.zip) i wystawia je wylacznie " +
                   "instalator - zadna aktualizacja ich nie przywroci.`n`n" +
                   "Uruchom ponownie instalator (installer\install.ps1) ze wskazana paczka " +
                   "(`$env:M2_SRC_ARCHIVE), albo rozpakuj metin2_mysql_dump.zip do tego katalogu " +
                   "i kliknij GRAJ jeszcze raz.")
        }
    }
    if ($missingContext.Count -gt 0) {
        throw ("Brakuje zrodel gry, wiec nie ma z czego zbudowac serwera.`n`n" +
               "Katalog: " + $gameContext + "`n" +
               "Brakuje: " + ($missingContext -join ', ') + "`n`n" +
               "To nie jest blad Dockera, WSL ani tej aktualizacji. Te pliki pochodza " +
               "z Twojej wlasnej paczki serwera r40250 i sa rozpakowywane raz, podczas " +
               "instalacji - zadna aktualizacja ich nie przywroci, bo nie wolno nam ich " +
               "rozpowszechniac.`n`n" +
               "Uruchom ponownie instalator (installer\install.ps1). Pobierze zrodla i " +
               "odtworzy kontekst budowania. Baza, postacie i ustawienia zostaja nietkniete.")
    }

    # See Stop-Server: compose progress on stderr must not be treated as failure
    # under $ErrorActionPreference='Stop' in Windows PowerShell 5.1.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        # `up --build` on a fresh engine has raced its own pull: the images
        # were built, then "No such image: mariadb:10.11" while creating the
        # database container, and the update was reported as failed although
        # the second click succeeded. Pull what is not built first; a failure
        # here is not final, `up` tries again.
        docker compose --project-directory $composeDir -f $composeFile pull --ignore-buildable 2>&1 | Out-Null
        Write-Phase 'Obrazy bazowe pobrane, zaczynam docker compose up --build'
        Set-M2PlayerbotsVersionEnvironment -ServerRoot $serverRoot
        docker compose --project-directory $composeDir -f $composeFile up -d --build
        $buildExit = $LASTEXITCODE
        Write-Phase "docker compose up --build zakonczone (kod $buildExit)"
    }
    finally { $ErrorActionPreference = $previousPreference }
    if ($buildExit -ne 0) {
        Set-Content -LiteralPath $rebuildMarkerPath -Value ([DateTime]::UtcNow.ToString('o')) -Encoding UTF8
        throw 'Nowa wersja plików została zapisana, ale Docker nie zbudował serwera. Kliknij GRAJ — launcher dokończy budowanie. Kopia plików jest w katalogu backups.'
    }
    if (Test-RebuildPending) { Remove-Item -LiteralPath $rebuildMarkerPath -Force -ErrorAction SilentlyContinue }
}

function Show-UpdateStatus {
    param($RemoteManifest)
    $state = Read-State
    $serverComponent = Get-ManifestComponent -RemoteManifest $RemoteManifest -Name 'server'
    $clientComponent = Get-ManifestComponent -RemoteManifest $RemoteManifest -Name 'client'
    $messageProperty = $RemoteManifest.PSObject.Properties['statusMessage']
    if ($null -ne $messageProperty -and [string]$messageProperty.Value) {
        Write-Host ([string]$messageProperty.Value) -ForegroundColor Yellow
    }
    Write-Host "Zainstalowany serwer: $($state.server)" -ForegroundColor Gray
    Write-Host "Dostępny serwer:     $(if ($serverComponent) { $serverComponent.version } else { 'brak w tym kanale' })" -ForegroundColor Cyan
    Write-Host "Zainstalowany klient: $($state.client)" -ForegroundColor Gray
    Write-Host "Dostępny klient:      $(if ($clientComponent) { $clientComponent.version } else { 'brak w tym kanale' })" -ForegroundColor Cyan
}

function Update-Server {
    param($RemoteManifest)
    $component = Get-ManifestComponent -RemoteManifest $RemoteManifest -Name 'server'
    if (-not $component) {
        Write-Host 'Manifest nie zawiera aktualizacji serwera. Pomijam.' -ForegroundColor Yellow
        return
    }
    $state = Read-State
    if (Test-InstalledVersion -Installed ([string]$state.server) -Available ([string]$component.version)) {
        Write-Host "Serwer jest już aktualny (wersja $($component.version))." -ForegroundColor Green
        return
    }
    if (-not (Confirm-Operation 'Zaktualizować pliki serwera i przebudować kontenery? Baza postaci pozostanie bez zmian.')) {
        Write-Host 'Anulowano.' -ForegroundColor Yellow
        return
    }
    $result = Invoke-M2PackageUpdate -Component $component -TargetRoot $serverRoot -BackupRoot (Join-Path $serverRoot 'backups')
    Write-Host "Podmieniono $($result.Files) plików. Kopia: $($result.Backup)" -ForegroundColor Green
    Write-Phase 'Pliki aktualizacji pobrane i podmienione'
    # From here the files on disk are the new version whatever happens to the
    # build, and VERSION on disk already says so. Recording it only after a
    # successful rebuild meant a deferred build left the launcher reporting the
    # previous version for ever - it kept offering the same update and kept
    # re-downloading and re-applying it, one backup directory per attempt. What
    # tracks the build is the rebuild marker, not the version number.
    Save-State -ServerVersion $result.Version -ClientVersion ''
    Rebuild-Server
    Write-Host "Serwer działa w wersji $($result.Version)." -ForegroundColor Green
}

function Update-Client {
    param($RemoteManifest, $Config)
    $component = Get-ManifestComponent -RemoteManifest $RemoteManifest -Name 'client'
    if (-not $component) {
        Write-Host 'Manifest nie zawiera aktualizacji klienta. Pomijam.' -ForegroundColor Yellow
        return
    }
    $state = Read-State
    if (Test-InstalledVersion -Installed ([string]$state.client) -Available ([string]$component.version)) {
        Write-Host "Klient jest już aktualny (wersja $($component.version))." -ForegroundColor Green
        return
    }
    $clientRoot = [string]$Config.clientRoot
    if (-not $clientRoot) {
        throw 'Nie ustawiono folderu klienta. Uruchom launcher z akcją Configure.'
    }
    if (-not (Test-Path -LiteralPath $clientRoot -PathType Container)) {
        throw "Nie znaleziono folderu klienta: $clientRoot"
    }
    if (-not (Confirm-Operation "Zaktualizować klienta w $clientRoot?")) {
        Write-Host 'Anulowano.' -ForegroundColor Yellow
        return
    }
    $result = Invoke-M2PackageUpdate -Component $component -TargetRoot $clientRoot -BackupRoot (Join-Path $serverRoot 'backups\client')
    Save-State -ServerVersion '' -ClientVersion $result.Version
    Write-Host "Klient został zaktualizowany. Plików: $($result.Files), kopia: $($result.Backup)" -ForegroundColor Green
}

function Configure-Launcher {
    $config = Get-Config
    Write-Host 'Pozostaw puste pole, aby zachować dotychczasową wartość.' -ForegroundColor Gray
    $manifestValue = Read-Host "Manifest aktualizacji [$($config.manifestUrl)]"
    if ($manifestValue) { $config.manifestUrl = $manifestValue }
    $clientValue = Read-Host "Folder klienta [$($config.clientRoot)]"
    if ($clientValue) { $config.clientRoot = [IO.Path]::GetFullPath($clientValue) }
    $clientExeValue = Read-Host "Plik EXE klienta [$($config.clientExecutable)]"
    if ($clientExeValue -eq '-') { $config.clientExecutable = '' }
    elseif ($clientExeValue) { $config.clientExecutable = [IO.Path]::GetFullPath($clientExeValue) }
    $supportState = if ($config.supportUploadUrl) { 'ustawiony' } else { 'nieustawiony' }
    $supportValue = Read-Host "Prywatny webhook Discord lub adres HTTPS pomocy [$supportState] (wpisz - aby usunąć)"
    if ($supportValue -eq '-') { $config.supportUploadUrl = '' }
    elseif ($supportValue) { $config.supportUploadUrl = $supportValue }
    Save-M2LauncherConfig -Config $config -ConfigPath $configPath
    Write-Host "Zapisano konfigurację: $configPath" -ForegroundColor Green
}

function Get-PlayerbotEnvPath {
    return Join-Path $serverRoot 'linux-port\docker\.env'
}

function Get-PlayerbotCount {
    $envPath = Get-PlayerbotEnvPath
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) { return 350 }
    $match = [Regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^PLAYERBOT_AUTOSPAWN_COUNT=(\d+)\s*$')
    if ($match.Success) { return [int]$match.Groups[1].Value }
    return 350
}

function Set-PlayerbotCount {
    # Writes PLAYERBOT_AUTOSPAWN_COUNT to .env. The core reads it once at startup
    # and spawns at most this many of the bots it will accept, which is a
    # different and usually smaller number: only characters the canonical seed
    # created are in the registry. A world carrying bots from an older bootstrap
    # keeps them, but they never spawn, so asking for more than the registry
    # holds simply gets the registry. The core says both numbers at startup:
    #   PLAYERBOT_AUTH: loaded <n> registered bot identities
    #   PLAYERBOT: autospawn requested=<x> registered_started=<n>
    #
    # The ceiling is the seed's canonical cohort: 1500 for Chunjo alone and 2500
    # once the other two kingdoms are switched on. This clamp is the one that
    # decides - the slider in the GUI only proposes a number, and raising that
    # alone would have written 1500 into .env while showing the player 2500.
    param([Parameter(Mandatory = $true)][int]$Count)
    if ($Count -lt 0) { $Count = 0 }
    if ($Count -gt 2500) { $Count = 2500 }
    $envPath = Get-PlayerbotEnvPath
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        throw "Brak pliku .env: $envPath. Uruchom najpierw serwer (GRAJ), aby go utworzyć."
    }
    $content = [IO.File]::ReadAllText($envPath)
    $pattern = '(?m)^PLAYERBOT_AUTOSPAWN_COUNT=.*$'
    if ([Regex]::IsMatch($content, $pattern)) {
        $content = [Regex]::Replace($content, $pattern, "PLAYERBOT_AUTOSPAWN_COUNT=$Count")
    }
    else {
        if ($content -and -not $content.EndsWith("`n")) { $content += [Environment]::NewLine }
        $content += "PLAYERBOT_AUTOSPAWN_COUNT=$Count" + [Environment]::NewLine
    }
    [IO.File]::WriteAllText($envPath, $content, [Text.UTF8Encoding]::new($false))
    return $Count
}

function Set-BotCountAction {
    $current = Get-PlayerbotCount
    Write-Host "Aktualnie gra: $current botów (efektywny limit = liczba botów w Twoim świecie; kanoniczna paczka ma 350)." -ForegroundColor Gray

    # -BotCount passed (from the GUI or scripting) is non-interactive: never call
    # Read-Host, because the GUI runs this in a hidden, non-interactive console.
    # Restart only when -Yes is also given. Without -BotCount we are in the text
    # menu and can prompt for both the number and the restart.
    if ($BotCount -ge 0) {
        $applied = Set-PlayerbotCount -Count $BotCount
        Write-Host "Zapisano: $applied grających botów." -ForegroundColor Green
        if ($Yes) {
            Start-Server
            Write-Host "Serwer zrestartowany z liczbą botów: $applied." -ForegroundColor Green
        }
        else {
            Write-Host 'Zmiana zostanie zastosowana przy następnym starcie serwera.' -ForegroundColor Yellow
        }
        return
    }

    $answer = Read-Host 'Ilu botów ma grać (0-2500)'
    if ($answer -notmatch '^\d+$') { Write-Host 'Anulowano: to nie jest liczba.' -ForegroundColor Yellow; return }
    $applied = Set-PlayerbotCount -Count ([int]$answer)
    Write-Host "Zapisano: $applied grających botów." -ForegroundColor Green
    if (Confirm-Operation 'Zrestartować serwer teraz, aby zastosować zmianę? Baza i postęp botów pozostają bez zmian') {
        Start-Server
        Write-Host "Serwer zrestartowany z liczbą botów: $applied." -ForegroundColor Green
    }
    else {
        Write-Host 'Zmiana zostanie zastosowana przy następnym starcie serwera.' -ForegroundColor Yellow
    }
}

function Get-CurrentInstallTargetVolume {
    # The db-data volume of THIS installation (import target).
    $statePath = Join-Path $serverRoot '.m2install.json'
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            $volProp = $state.PSObject.Properties['databaseVolume']
            if ($volProp -and [string]$volProp.Value) { return [string]$volProp.Value }
            if ([string]$state.projectName) { return "$([string]$state.projectName)_db-data" }
        }
        catch { }
    }
    $envPath = Join-Path $serverRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = [Regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^M2_COMPOSE_PROJECT_NAME=([a-z0-9][a-z0-9_-]+)\s*$')
        if ($match.Success) { return "$($match.Groups[1].Value)_db-data" }
    }
    return $null
}

function Import-DatabaseAction {
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany, więc nie widać żadnych baz.' -ForegroundColor Yellow
        Write-Host 'Uruchom Docker (akcja StartDocker lub przycisk „URUCHOM DOCKER") i spróbuj ponownie.' -ForegroundColor Yellow
        Write-Host 'Żadne dane nie zginęły — bazy są na dysku, tylko Docker ich teraz nie pokazuje.' -ForegroundColor Gray
        return
    }
    $target = Get-CurrentInstallTargetVolume
    if (-not $target) {
        Write-Host 'Nie można ustalić bazy tej instalacji. Uruchom najpierw serwer (GRAJ) choć raz, aby utworzyć tożsamość i wolumen.' -ForegroundColor Yellow
        return
    }
    Write-Host "Baza docelowa (ta instalacja): $target" -ForegroundColor Gray
    if (-not (Test-M2VolumeInitialized -Volume $target)) {
        Write-Host 'Ta instalacja nie ma jeszcze gotowej bazy danych.' -ForegroundColor Yellow
        Write-Host 'Najpierw kliknij GRAJ i pozwól serwerowi wystartować choć raz (utworzy bazę ze schematami gry),' -ForegroundColor Yellow
        Write-Host 'a dopiero potem importuj świat. Import na pustą bazę zostawiłby instalację bez schematów.' -ForegroundColor Yellow
        return
    }
    $sources = @(Get-M2DbDataVolumes | Where-Object { $_.Name -ne $target })
    if ($sources.Count -eq 0) {
        Write-Host 'Nie znaleziono innej bazy Docker do importu na tym komputerze.' -ForegroundColor Yellow
        return
    }

    $chosen = $null
    if ($ImportSource) {
        $chosen = $sources | Where-Object { $_.Name -eq $ImportSource -or $_.Project -eq $ImportSource } | Select-Object -First 1
        if (-not $chosen) { Write-Host "Nie znaleziono źródła do importu: $ImportSource" -ForegroundColor Red; return }
    }
    else {
        Write-Host 'Dostępne bazy do importu:' -ForegroundColor Cyan
        for ($i = 0; $i -lt $sources.Count; $i++) {
            $label = $sources[$i].Project
            if ($sources[$i].CreatedAt) { $label = '{0}   (utworzona {1:yyyy-MM-dd HH:mm})' -f $label, $sources[$i].CreatedAt }
            Write-Host ("  [{0}] {1}" -f ($i + 1), $label)
        }
        $pick = Read-Host 'Wybierz numer źródła (Enter = anuluj)'
        if ($pick -notmatch '^\d+$') { Write-Host 'Anulowano.' -ForegroundColor Yellow; return }
        $idx = [int]$pick - 1
        if ($idx -lt 0 -or $idx -ge $sources.Count) { Write-Host 'Nieprawidłowy numer.' -ForegroundColor Yellow; return }
        $chosen = $sources[$idx]
    }

    Write-Host "Sprawdzam świat źródłowy '$($chosen.Project)'..." -ForegroundColor Gray
    $stats = Get-M2VolumeWorldStats -Volume $chosen.Name
    if ($stats.Ok) {
        Write-Host ("Źródło: {0} postaci, najwyższy poziom {1}." -f $stats.Players, $stats.MaxLevel) -ForegroundColor Green
        if ($stats.Created) { Write-Host ("  Baza utworzona: {0}" -f $stats.Created) -ForegroundColor Gray }
        if ($stats.LastPlay -and $stats.LastPlay -ne '0') { Write-Host ("  Ostatnia gra: {0}" -f $stats.LastPlay) -ForegroundColor Gray }
    }
    else {
        Write-Host 'Nie udało się odczytać statystyk źródła (mimo to można spróbować importu).' -ForegroundColor Yellow
    }

    Write-Host ''
    Write-Host "UWAGA: import ZASTĄPI obecny świat tej instalacji światem ze źródła '$($chosen.Project)'." -ForegroundColor Yellow
    Write-Host "Źródło pozostaje nietknięte. Obecny świat trafi do kopii w 'backups' przed nadpisaniem." -ForegroundColor Yellow
    if (-not (Confirm-Operation "Kontynuować import z '$($chosen.Project)'?")) { Write-Host 'Anulowano.' -ForegroundColor Yellow; return }

    # Read this install's game DB user/password so the import can re-apply the
    # user and grants afterwards (guards against the migrator failing to
    # authenticate after a swap).
    $dbUser = 'metin2'; $dbPass = ''
    $importEnvPath = Join-Path $serverRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $importEnvPath -PathType Leaf) {
        $importEnvText = [IO.File]::ReadAllText($importEnvPath)
        $userMatch = [Regex]::Match($importEnvText, '(?m)^M2_DB_USER=(.+?)\s*$')
        if ($userMatch.Success) { $dbUser = $userMatch.Groups[1].Value }
        $passMatch = [Regex]::Match($importEnvText, '(?m)^M2_DB_PASSWORD=(.+?)\s*$')
        if ($passMatch.Success) { $dbPass = $passMatch.Groups[1].Value }
    }

    Write-Host 'Zatrzymuję serwer, aby zwolnić bazę docelową...' -ForegroundColor Cyan
    Stop-Server

    Write-Host 'Importuję bazę (to może potrwać chwilę)...' -ForegroundColor Cyan
    $result = Invoke-M2DatabaseImport -SourceVolume $chosen.Name -TargetVolume $target -BackupRoot (Join-Path $serverRoot 'backups') -DbUser $dbUser -DbPassword $dbPass
    Write-Host ("Gotowe. Zaimportowany świat: {0} postaci, najwyższy poziom {1}." -f $result.Players, $result.MaxLevel) -ForegroundColor Green
    Write-Host ("Kopia poprzedniego świata: {0}" -f $result.Backup) -ForegroundColor Gray
    Write-Host 'Kliknij GRAJ (lub akcja Start), aby uruchomić serwer z zaimportowanym światem.' -ForegroundColor Green
}

function Backup-DatabaseAction {
    # Everything the import path already did to protect a world, asked for on
    # purpose instead of as a side effect: five SQL dumps, a manifest and a zip.
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany, wiec nie da sie odczytac bazy.' -ForegroundColor Yellow
        Write-Host 'Uruchom Docker (akcja StartDocker) i sprobuj ponownie. Nic nie zginelo.' -ForegroundColor Gray
        return
    }
    $target = Get-CurrentInstallTargetVolume
    if (-not $target) {
        Write-Host 'Nie mozna ustalic bazy tej instalacji. Uruchom najpierw serwer (GRAJ) choc raz.' -ForegroundColor Yellow
        return
    }
    if (-not (Test-M2VolumeInitialized -Volume $target)) {
        Write-Host 'Ta instalacja nie ma jeszcze bazy danych - nie ma czego zapisac.' -ForegroundColor Yellow
        return
    }
    Write-Host 'Zatrzymuję serwer, aby baza była spójna w chwili zapisu...' -ForegroundColor Cyan
    Stop-Server
    Write-Host 'Zapisuję kopię (to może potrwać chwilę)...' -ForegroundColor Cyan
    $result = New-M2DatabaseBackup -Volume $target -BackupRoot (Join-Path $serverRoot 'backups')
    Write-Host ("Gotowe. Zapisany świat: {0} postaci, najwyższy poziom {1}." -f $result.Players, $result.MaxLevel) -ForegroundColor Green
    Write-Host ("  Folder: {0}" -f $result.Folder) -ForegroundColor Gray
    Write-Host ("  Plik:   {0}  ({1:N0} MB)" -f $result.Zip, ($result.ZipBytes / 1MB)) -ForegroundColor Gray
    Write-Host 'Ten jeden plik zip wystarczy, aby odtworzyć świat na tym albo na innym komputerze.' -ForegroundColor Gray
    Write-Host 'Kliknij GRAJ, aby uruchomić serwer z powrotem.' -ForegroundColor Green
}

function Restore-DatabaseAction {
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany. Uruchom Docker i spróbuj ponownie.' -ForegroundColor Yellow
        return
    }
    $target = Get-CurrentInstallTargetVolume
    if (-not $target) {
        Write-Host 'Nie mozna ustalic bazy tej instalacji. Uruchom najpierw serwer (GRAJ) choc raz.' -ForegroundColor Yellow
        return
    }
    $picked = $RestoreSource
    if (-not $picked) {
        $backupRoot = Join-Path $serverRoot 'backups'
        $found = @()
        if (Test-Path -LiteralPath $backupRoot -PathType Container) {
            $found = @(Get-ChildItem -LiteralPath $backupRoot -Filter 'db-backup-*.zip' -File |
                       Sort-Object LastWriteTime -Descending)
        }
        if ($found.Count -eq 0) {
            Write-Host "Nie znaleziono zadnej kopii w '$backupRoot'." -ForegroundColor Yellow
            Write-Host 'Zrob najpierw kopie (akcja BackupDb), albo podaj sciezke: -RestoreSource "C:\...\db-backup-....zip"' -ForegroundColor Gray
            return
        }
        Write-Host 'Dostępne kopie:' -ForegroundColor Cyan
        for ($i = 0; $i -lt $found.Count; $i++) {
            Write-Host ("  [{0}] {1}   ({2:yyyy-MM-dd HH:mm}, {3:N0} MB)" -f ($i + 1),
                $found[$i].Name, $found[$i].LastWriteTime, ($found[$i].Length / 1MB))
        }
        $pick = Read-Host 'Wybierz numer kopii (Enter = anuluj)'
        if ($pick -notmatch '^\d+$') { Write-Host 'Anulowano.' -ForegroundColor Yellow; return }
        $idx = [int]$pick - 1
        if ($idx -lt 0 -or $idx -ge $found.Count) { Write-Host 'Nieprawidłowy numer.' -ForegroundColor Yellow; return }
        $picked = $found[$idx].FullName
    }
    if (-not (Test-Path -LiteralPath $picked)) {
        Write-Host "Nie znaleziono kopii: $picked" -ForegroundColor Red
        return
    }
    Write-Host ''
    Write-Host "UWAGA: przywrócenie ZASTĄPI obecny świat tej instalacji zawartością kopii." -ForegroundColor Yellow
    Write-Host 'Obecny świat zostanie najpierw zapisany do własnej kopii w folderze backups.' -ForegroundColor Yellow
    if (-not (Confirm-Operation "Przywrócić świat z '$([IO.Path]::GetFileName($picked))'?")) {
        Write-Host 'Anulowano.' -ForegroundColor Yellow; return
    }
    $creds = Get-InstallDbCredentials
    Write-Host 'Zatrzymuję serwer, aby zwolnić bazę...' -ForegroundColor Cyan
    Stop-Server
    Write-Host 'Przywracam kopię (to może potrwać chwilę)...' -ForegroundColor Cyan
    $result = Restore-M2DatabaseBackup -BackupPath $picked -TargetVolume $target `
        -BackupRoot (Join-Path $serverRoot 'backups') -DbUser $creds.User -DbPassword $creds.Password
    Write-Host ("Gotowe. Przywrócony świat: {0} postaci, najwyższy poziom {1}." -f $result.Players, $result.MaxLevel) -ForegroundColor Green
    Write-Host ("  Kopia poprzedniego świata: {0}" -f $result.Safety) -ForegroundColor Gray
    Write-Host 'Kliknij GRAJ, aby uruchomić serwer z przywróconym światem.' -ForegroundColor Green
}

function Reset-WorldAction {
    # "Zacznij od zera": the world a fresh install starts with, with the old one
    # kept as a zip. The volume is deleted, because that is the only thing that
    # makes MariaDB import initdb.d again.
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany. Uruchom Docker i spróbuj ponownie.' -ForegroundColor Yellow
        return
    }
    $target = Get-CurrentInstallTargetVolume
    if (-not $target) {
        Write-Host 'Nie mozna ustalic bazy tej instalacji.' -ForegroundColor Yellow
        return
    }
    $missing = @(Get-M2MissingSqlDumps -ServerRoot $serverRoot)
    if ($missing.Count -gt 0) {
        Write-Host 'Nie mogę zresetować świata: brakuje zrzutów, z których powstaje nowa baza.' -ForegroundColor Red
        Write-Host ('  Brakuje: ' + ($missing -join ', ')) -ForegroundColor Red
        Write-Host '  Miejsce: linux-port\docker\mariadb\initdb.d\dumps' -ForegroundColor Gray
        Write-Host 'Bez nich skasowanie bazy zostawiłoby instalację bez świata i bez sposobu na nowy.' -ForegroundColor Gray
        return
    }
    Write-Host ''
    Write-Host 'UWAGA: to kasuje CAŁY obecny świat - postacie, poziomy, ekwipunek, boty, konta gry.' -ForegroundColor Yellow
    Write-Host 'Przed skasowaniem świat zostanie zapisany do kopii zip w folderze backups,' -ForegroundColor Yellow
    Write-Host 'więc da się do niego wrócić akcją "Przywróć kopię".' -ForegroundColor Yellow
    Write-Host 'Po resecie pierwszy start potrwa dłużej: baza powstaje od nowa i boty są zasiewane.' -ForegroundColor Gray
    if (-not (Confirm-Operation 'Zresetować świat do stanu świeżej instalacji?')) {
        Write-Host 'Anulowano.' -ForegroundColor Yellow; return
    }
    Write-Host 'Zatrzymuję serwer i Dockera po stronie stosu...' -ForegroundColor Cyan
    Stop-Server
    Write-Host 'Zapisuję kopię i kasuję bazę...' -ForegroundColor Cyan
    $result = Reset-M2WorldToFreshInstall -Volume $target -ServerRoot $serverRoot `
        -BackupRoot (Join-Path $serverRoot 'backups')
    if ($result.Backup) {
        Write-Host ("Kopia poprzedniego świata ({0} postaci): {1}" -f $result.Players, $result.Backup) -ForegroundColor Gray
    }
    Write-Host 'Świat skasowany. Kliknij GRAJ - serwer zbuduje bazę od nowa i zasieje boty.' -ForegroundColor Green
}

function Reset-PanelPasswordAction {
    # The panel keeps a PBKDF2 hash of its passphrase in m2panel.conf, on a
    # volume of its own, and its entrypoint never regenerates it - regenerating
    # would log every operator out and invalidate every session cookie. Right,
    # except when the passphrase it hashed is one nobody has: the container
    # invented it on a first run and printed it to a log nobody read.
    #
    # Deleting that one file is the whole reset. The entrypoint then rebuilds it
    # from M2_PANEL_PASSWORD, which the launcher now guarantees is in .env.
    $creds = Get-InstallDbCredentials
    $panelPw = ''
    if ($creds.EnvPath) {
        $text = [IO.File]::ReadAllText($creds.EnvPath)
        $match = [Regex]::Match($text, '(?m)^M2_PANEL_PASSWORD=(.+?)\s*$')
        if ($match.Success) { $panelPw = $match.Groups[1].Value }
    }
    if (-not $panelPw) {
        Write-Host 'W pliku .env nie ma hasla do panelu. Uruchom raz GRAJ - launcher je uzupelni i pokaze.' -ForegroundColor Yellow
        return
    }
    Write-Host 'Haslo do panelu WWW (z pliku linux-port\docker\.env):' -ForegroundColor Cyan
    Write-Host "  $panelPw"
    Write-Host ''
    Write-Host 'Jesli panel go nie przyjmuje, znaczy to, ze zapamietal starsze haslo.' -ForegroundColor Gray
    Write-Host 'Reset kasuje jeden plik konfiguracyjny panelu; swiat, postacie i boty' -ForegroundColor Gray
    Write-Host 'sa w bazie i nie sa tym ruszane. Wylogowuje otwarte sesje panelu.' -ForegroundColor Gray
    if (-not (Confirm-Operation 'Zresetowac haslo panelu do tego z .env?')) {
        Write-Host 'Anulowano - haslo wyzej pozostaje aktualne.' -ForegroundColor Yellow
        return
    }
    # The panel's config volume is named after the same project as the database
    # volume, which the launcher already knows how to find.
    $dbVolume = Get-CurrentInstallTargetVolume
    if (-not $dbVolume -or -not $dbVolume.EndsWith('_db-data')) {
        Write-Host 'Nie moge ustalic nazwy projektu tej instalacji. Uruchom raz GRAJ.' -ForegroundColor Yellow
        return
    }
    $volume = $dbVolume.Substring(0, $dbVolume.Length - '_db-data'.Length) + '_panel-conf'

    $composeDir = Join-Path $serverRoot 'linux-port\docker'
    $composeFile = Join-Path $composeDir 'docker-compose.yml'
    $previousPreference = $ErrorActionPreference
    try {
        # docker compose writes progress to stderr; under 'Stop' that is a
        # terminating error even when the command worked. See Stop-Server.
        $ErrorActionPreference = 'Continue'
        Write-Host 'Zatrzymuje panel...' -ForegroundColor Cyan
        docker compose --project-directory $composeDir -f $composeFile stop panel 2>&1 | Out-Null
        Write-Host 'Kasuje zapamietane haslo...' -ForegroundColor Cyan
        docker run --rm -v "${volume}:/etc/m2panel" alpine:3.20 rm -f /etc/m2panel/m2panel.conf 2>&1 | Out-Null
        $removeExit = $LASTEXITCODE
        if ($removeExit -ne 0) {
            Write-Host "Nie udalo sie skasowac pliku (kod $removeExit). Panel zostaje bez zmian." -ForegroundColor Red
            docker compose --project-directory $composeDir -f $composeFile start panel 2>&1 | Out-Null
            return
        }
        Write-Host 'Uruchamiam panel...' -ForegroundColor Cyan
        docker compose --project-directory $composeDir -f $composeFile up -d --no-deps panel 2>&1 | Out-Null
    }
    finally { $ErrorActionPreference = $previousPreference }

    Write-Host ''
    Write-Host 'Gotowe. Zaloguj sie haslem:' -ForegroundColor Green
    Write-Host "  $panelPw"
}

function Get-InstallDbCredentials {
    # Everything a database client needs, straight from .env: the port the
    # compose file publishes on 127.0.0.1, the game account and root. The root
    # password is what MariaDB was initialised with, and what Repair-DatabaseAction
    # puts back on root@'%' when the two have drifted apart.
    $result = [pscustomobject]@{ User = 'metin2'; Password = ''; RootPassword = ''; Port = '3306'; EnvPath = '' }
    $envPath = Join-Path $serverRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $result.EnvPath = $envPath
        $text = [IO.File]::ReadAllText($envPath)
        $userMatch = [Regex]::Match($text, '(?m)^M2_DB_USER=(.+?)\s*$')
        if ($userMatch.Success) { $result.User = $userMatch.Groups[1].Value }
        $passMatch = [Regex]::Match($text, '(?m)^M2_DB_PASSWORD=(.+?)\s*$')
        if ($passMatch.Success) { $result.Password = $passMatch.Groups[1].Value }
        $rootMatch = [Regex]::Match($text, '(?m)^M2_DB_ROOT_PASSWORD=(.+?)\s*$')
        if ($rootMatch.Success) { $result.RootPassword = $rootMatch.Groups[1].Value }
        $portMatch = [Regex]::Match($text, '(?m)^M2_DB_PUBLISH_PORT=(\d+)\s*$')
        if ($portMatch.Success) { $result.Port = $portMatch.Groups[1].Value }
    }
    return $result
}

function Show-DatabaseAccessAction {
    # Where a database client (Navicat, HeidiSQL, DBeaver) connects, and with
    # which accounts. The passwords are not printed: this output lands in the
    # launcher log, and the launcher log lands in support bundles that get
    # posted on the Discord. The GUI shows them in a dialog of its own; here
    # the .env is opened in Notepad instead.
    $creds = Get-InstallDbCredentials
    if (-not $creds.EnvPath) {
        Write-Host 'Brak pliku linux-port\docker\.env — uruchom najpierw serwer (GRAJ), launcher go utworzy.' -ForegroundColor Yellow
        return
    }
    Write-Host 'Dane do połączenia z bazą (Navicat, HeidiSQL, DBeaver — typ MySQL/MariaDB):' -ForegroundColor Cyan
    Write-Host '  Host:      127.0.0.1'
    Write-Host "  Port:      $($creds.Port)"
    Write-Host '  Konto 1:   root        — pełny dostęp; hasło: M2_DB_ROOT_PASSWORD w pliku .env'
    Write-Host "  Konto 2:   $($creds.User)      — tylko bazy gry; hasło: M2_DB_PASSWORD w pliku .env"
    Write-Host "  Plik .env: $($creds.EnvPath)"
    Write-Host ''
    Write-Host 'Baza słucha tylko na tym komputerze (127.0.0.1), więc klient musi działać na nim.' -ForegroundColor Gray
    if ((Get-M2ServerEngine -ServerRoot $serverRoot) -ne 'r40250') {
        Write-Host 'Na plikach 2.x przedmioty i potwory (item_proto, mob_proto) są w bazie world; player.item_proto' -ForegroundColor Gray
        Write-Host 'i player.mob_proto to tylko widoki. Zmiany w world zostają po restarcie serwera.' -ForegroundColor Gray
    }
    Write-Host 'Jeśli baza odrzuca hasło z .env („Access denied"), użyj akcji RepairDb (przycisk' -ForegroundColor Gray
    Write-Host '„NAPRAW DOSTĘP DO BAZY"): ustawia konta root i metin2 na hasła z tego pliku.' -ForegroundColor Gray
    Write-Host 'Nie wklejaj haseł z .env na Discordzie ani do paczki z logami.' -ForegroundColor Yellow
    if (-not $Yes) {
        $answer = Read-Host 'Otworzyć plik .env w Notatniku, żeby skopiować hasła? [t/N]'
        if ($answer -match '^[tTyY]') { Start-Process notepad.exe -ArgumentList ('"' + $creds.EnvPath + '"') }
    }
}

function Repair-DatabaseAction {
    if (-not (Test-M2DockerRunning)) {
        Write-Host 'Silnik Dockera jest zatrzymany, więc nie widać żadnych baz.' -ForegroundColor Yellow
        Write-Host 'Uruchom Docker (akcja StartDocker lub przycisk „URUCHOM DOCKER") i spróbuj ponownie.' -ForegroundColor Yellow
        Write-Host 'Żadne dane nie zginęły — bazy są na dysku, tylko Docker ich teraz nie pokazuje.' -ForegroundColor Gray
        return
    }
    $target = Get-CurrentInstallTargetVolume
    if (-not $target) {
        Write-Host 'Nie można ustalić bazy tej instalacji. Uruchom najpierw serwer (GRAJ) choć raz.' -ForegroundColor Yellow
        return
    }
    $creds = Get-InstallDbCredentials
    if (-not $creds.Password) {
        Write-Host 'Brak M2_DB_PASSWORD w linux-port\docker\.env — nie mam czego przywrócić.' -ForegroundColor Red
        return
    }
    Write-Host "Naprawiam konta bazy dla instalacji: $target" -ForegroundColor Cyan
    Write-Host 'To odtwarza wyłącznie użytkowników i uprawnienia bazy — konto gry i root — z hasłami z pliku .env. Postacie, przedmioty i boty pozostają bez zmian.' -ForegroundColor Gray
    if (-not $creds.RootPassword) {
        Write-Host 'Brak M2_DB_ROOT_PASSWORD w .env — konto root zostanie pominięte.' -ForegroundColor Yellow
    }
    Write-Host 'Zatrzymuję serwer, aby zwolnić bazę...' -ForegroundColor Cyan
    Stop-Server
    if (Repair-M2GameDbUser -Volume $target -DbUser $creds.User -DbPassword $creds.Password -RootPassword $creds.RootPassword) {
        Write-Host 'Gotowe. Konta i uprawnienia bazy odtworzone. Kliknij GRAJ, aby uruchomić serwer.' -ForegroundColor Green
        Write-Host "Do Navicat: host 127.0.0.1, port $($creds.Port), root albo $($creds.User) — hasła z .env (akcja DbAccess pokaże szczegóły)." -ForegroundColor Gray
    }
    else {
        Write-Host 'Naprawa nie powiodła się. Zbierz logi (ZIP) i zgłoś problem.' -ForegroundColor Red
    }
}

function Create-Logs {
    $preflightLog = Join-Path $serverRoot 'launcher-logs\preflight-last.log'
    New-Item -ItemType Directory -Path (Split-Path -Parent $preflightLog) -Force | Out-Null
    $report = Get-M2DockerPreflight -ServerRoot $serverRoot -CheckPanelPort
    [IO.File]::WriteAllText(
        $preflightLog,
        (Format-M2DockerPreflightReport -Report $report),
        [Text.UTF8Encoding]::new($false))
    $bundle = New-M2SupportBundle -ServerRoot $serverRoot
    Write-Host "Gotowa paczka diagnostyczna: $bundle" -ForegroundColor Green
    return $bundle
}

function Send-Logs {
    $config = Get-Config
    $support = Get-M2SupportSettings -Config $config
    if (-not $support.UploadUrl) {
        throw "Kanał zgłoszeń jest teraz niedostępny. Utwórz ZIP akcją Logs i wyślij go ręcznie na Discordzie: $($support.ContactUrl)"
    }
    $bundle = Create-Logs
    Write-Host 'Paczka zawiera logi Dockera i konfigurację z usuniętymi hasłami.' -ForegroundColor Yellow
    $target = if ($support.Source -eq 'manifest') { 'kanału zgłoszeń autora' } else { $support.UploadUrl }
    if (-not (Confirm-Operation "Wysłać $bundle do $target?")) {
        Write-Host 'Nie wysłano. ZIP pozostał na dysku.' -ForegroundColor Yellow
        return
    }
    $response = Send-M2SupportBundle -BundlePath $bundle -UploadUrl $support.UploadUrl
    if ($response) { Write-Host "Wysłano. Odpowiedź serwera: $response" -ForegroundColor Green }
    else { Write-Host 'Wysłano paczkę diagnostyczną.' -ForegroundColor Green }
}

function Invoke-Action {
    param([Parameter(Mandatory = $true)][string]$SelectedAction)
    $config = Get-Config
    switch ($SelectedAction) {
        'Start' { Start-Server }
        'Stop' { Stop-Server }
        'StartDocker' { Start-Docker }
        'StopAll' { Stop-DockerAndServer }
        'Check' {
            $remote = Get-M2UpdateManifest -Source (Get-ManifestSource $config)
            Show-UpdateStatus -RemoteManifest $remote
        }
        'UpdateServer' {
            $remote = Get-M2UpdateManifest -Source (Get-ManifestSource $config)
            Show-UpdateStatus -RemoteManifest $remote
            Update-Server -RemoteManifest $remote
        }
        'UpdateClient' {
            $remote = Get-M2UpdateManifest -Source (Get-ManifestSource $config)
            Show-UpdateStatus -RemoteManifest $remote
            Update-Client -RemoteManifest $remote -Config $config
        }
        'UpdateAll' {
            $remote = Get-M2UpdateManifest -Source (Get-ManifestSource $config)
            Show-UpdateStatus -RemoteManifest $remote
            Update-Server -RemoteManifest $remote
            Update-Client -RemoteManifest $remote -Config $config
        }
        'Diagnose' { Show-DockerDiagnostics -CheckPanelPort | Out-Null }
        'Logs' { Create-Logs | Out-Null }
        'SendLogs' { Send-Logs }
        'Configure' { Configure-Launcher }
        'SetBots' { Set-BotCountAction }
        'ImportDb' { Import-DatabaseAction }
        'BackupDb' { Backup-DatabaseAction }
        'RestoreDb' { Restore-DatabaseAction }
        'ResetWorld' { Reset-WorldAction }
        'RepairDb' { Repair-DatabaseAction }
        'DbAccess' { Show-DatabaseAccessAction }
        'PanelPassword' { Reset-PanelPasswordAction }
        default { throw "Nieznana akcja: $SelectedAction" }
    }
}

function Show-Menu {
    while ($true) {
        Write-Header
        Write-Host '  1. Uruchom serwer'
        Write-Host '  2. Zatrzymaj serwer'
        Write-Host '  3. Uruchom tylko Docker Desktop'
        Write-Host '  4. Zatrzymaj serwer i Docker (postęp zostaje)'
        Write-Host '  5. Sprawdź aktualizacje'
        Write-Host '  6. Aktualizuj serwer'
        Write-Host '  7. Aktualizuj klienta'
        Write-Host '  8. Aktualizuj wszystko'
        Write-Host '  9. Sprawdź Docker, WSL, wirtualizację i porty'
        Write-Host ' 10. Utwórz paczkę diagnostyczną ZIP'
        Write-Host ' 11. Utwórz i wyślij logi (po potwierdzeniu)'
        Write-Host ' 12. Konfiguracja launchera'
        Write-Host ' 13. Ustaw liczbę grających botów (0-2500)'
        Write-Host ' 14. Importuj bazę z innej instalacji (wyższe postacie)'
        Write-Host ' 15. Zapisz kopię świata (backup do pliku zip)'
        Write-Host ' 16. Przywróć świat z kopii'
        Write-Host ' 17. Zresetuj świat do stanu świeżej instalacji (kopia zapisywana automatycznie)'
        Write-Host ' 18. Napraw dostęp do bazy (gdy migrate/serwer nie startuje albo Navicat odrzuca hasło)'
        Write-Host ' 19. Dane do połączenia z bazą (Navicat, HeidiSQL)'
        Write-Host ' 20. Hasło do panelu WWW (pokaż / zresetuj)'
        Write-Host '  0. Wyjście'
        Write-Host ''
        $choice = Read-Host 'Wybierz opcję'
        $selected = switch ($choice) {
            '1' { 'Start' } '2' { 'Stop' } '3' { 'StartDocker' } '4' { 'StopAll' }
            '5' { 'Check' } '6' { 'UpdateServer' } '7' { 'UpdateClient' }
            '8' { 'UpdateAll' } '9' { 'Diagnose' } '10' { 'Logs' } '11' { 'SendLogs' } '12' { 'Configure' }
            '13' { 'SetBots' }
            '14' { 'ImportDb' }
            '15' { 'BackupDb' }
            '16' { 'RestoreDb' }
            '17' { 'ResetWorld' }
            '18' { 'RepairDb' }
            '19' { 'DbAccess' }
            '20' { 'PanelPassword' }
            '0' { return }
            default { '' }
        }
        if (-not $selected) { continue }
        try { Invoke-Action -SelectedAction $selected }
        catch { Write-Host "BŁĄD: $($_.Exception.Message)" -ForegroundColor Red }
        Write-Host ''
        Read-Host 'Naciśnij Enter, aby wrócić do menu' | Out-Null
    }
}

try {
    if ($Action -eq 'Menu') { Show-Menu }
    else { Invoke-Action -SelectedAction $Action }
}
catch {
    Write-Host "BŁĄD: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
