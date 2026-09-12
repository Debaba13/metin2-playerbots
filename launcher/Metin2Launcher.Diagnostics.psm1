Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Invoke-M2DiagnosticProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FileName,
        [AllowEmptyString()][string]$Arguments = '',
        [ValidateRange(100, 30000)][int]$TimeoutMilliseconds = 3500
    )

    $process = $null
    try {
        $startInfo = [Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $FileName
        $startInfo.Arguments = $Arguments
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = [Diagnostics.Process]::Start($startInfo)
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill() } catch {}
            return [pscustomobject]@{
                ExitCode = -1
                TimedOut = $true
                Output = 'Polecenie nie odpowiedziało w wyznaczonym czasie.'
            }
        }
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        return [pscustomobject]@{
            ExitCode = $process.ExitCode
            TimedOut = $false
            Output = ($stdout + $stderr).Trim()
        }
    }
    catch {
        return [pscustomobject]@{
            ExitCode = -1
            TimedOut = $false
            Output = $_.Exception.Message
        }
    }
    finally {
        if ($process) { $process.Dispose() }
    }
}

function Get-M2LauncherErrorGuidance {
    param([AllowEmptyString()][string]$Text)

    $value = [string]$Text
    $port = '7788'
    if ($value -match '(?i)(?:Bind for |listen (?:tcp )?)(?:\[?[^\]\s:]+\]?:)?(?<port>\d{2,5})') {
        $port = $Matches.port
    }
    elseif ($value -match '(?i)(?<port>\d{2,5}).{0,80}(?:port is already allocated|address already in use)') {
        $port = $Matches.port
    }

    # Not a busy port: Windows itself refused the bind. Hyper-V and WSL reserve
    # random port ranges after a restart ("excluded port ranges"), and when
    # 11000 or 13000 falls inside one, compose fails one second after the
    # images are built with a message about access permissions. Five updates
    # in a row went that way for one player before this branch existed.
    if ($value -match '(?i)ports are not available|forbidden by its access permissions|zabroniony przez uprawnienia|WSAEACCES|\b10013\b') {
        return [pscustomobject]@{
            Code = 'PORT_EXCLUDED'
            Title = "Windows zarezerwował port $port"
            Message = "Port $port nie jest zajęty przez program - jest w zakresie, który Windows (Hyper-V/WSL) zarezerwował dla siebie po ostatnim restarcie. Docker nie może na nim nasłuchiwać, więc serwer nie wstaje. Pliki serwera i baza są w porządku."
            Remedy = 'Uruchom PowerShell jako administrator i wykonaj: net stop winnat, potem kliknij GRAJ w launcherze, a gdy serwer wstanie, wykonaj: net start winnat. Zwykle pomaga też zwykły restart Windows. Sprawdzenie zakresów: netsh interface ipv4 show excludedportrange protocol=tcp'
        }
    }

    if ($value -match '(?i)port is already allocated|address already in use|failed programming external connectivity|bind for .+ failed|port \d{2,5} (?:jest zajęty|zajmuje)') {
        return [pscustomobject]@{
            Code = 'PORT_IN_USE'
            Title = "Port $port jest już zajęty"
            Message = "Inny program albo druga instalacja serwera używa portu $port. Launcher nie uruchomi drugiego serwera na tym samym porcie."
            Remedy = 'Zamknij poprzednią instalację przyciskiem „Zatrzymaj i zapisz” albo korzystaj z launchera znajdującego się w folderze już uruchomionego serwera. Nie usuwaj wolumenów Dockera.'
        }
    }

    if ($value -match '(?i)virtuali[sz]ation support (?:(?:wasn.t |was )?not )?detected|hardware.assisted virtuali[sz]ation|virtuali[sz]ation.*disabled') {
        return [pscustomobject]@{
            Code = 'VIRTUALIZATION_DISABLED'
            Title = 'Wirtualizacja jest wyłączona'
            Message = 'Docker Desktop nie wystartuje, dopóki wirtualizacja procesora nie będzie dostępna dla Windows.'
            Remedy = 'W BIOS/UEFI włącz AMD SVM/AMD-V albo Intel VT-x. Następnie włącz funkcje „Virtual Machine Platform” i „Windows Subsystem for Linux”, uruchom jako administrator: wsl --install, po czym zrestartuj komputer.'
        }
    }

    if ($value -match '(?i)there was a problem with wsl|wsl.+(?:error|failed|exit status)|Wsl/Service/|WSL 2 installation is incomplete|windows subsystem for linux.+(?:missing|disabled)') {
        return [pscustomobject]@{
            Code = 'WSL_BROKEN'
            Title = 'WSL 2 wymaga naprawy'
            Message = 'Docker Desktop nie może uruchomić swojego środowiska WSL 2.'
            Remedy = 'Otwórz PowerShell jako administrator i wykonaj kolejno: wsl --status, wsl --update oraz wsl --install. Zrestartuj Windows. Jeżeli błąd pozostanie, sprawdź czy w BIOS/UEFI jest włączone AMD SVM/Intel VT-x.'
        }
    }

    if ($value -match '(?i)docker engine did not become ready|cannot connect to the docker daemon|open //./pipe/docker|docker desktop is unable to start|docker api is unavailable') {
        return [pscustomobject]@{
            Code = 'DOCKER_NOT_READY'
            Title = 'Docker Engine nie jest jeszcze gotowy'
            Message = 'Okno Docker Desktop może być otwarte, ale jego silnik nadal startuje albo zatrzymał się na błędzie.'
            Remedy = 'Odczekaj chwilę i spróbuj ponownie. Jeśli status nie zmieni się na „GOTOWY”, otwórz Docker Desktop → Troubleshoot → Restart. Potem użyj w launcherze „Diagnostyka” i „Zbierz logi (ZIP)”.'
        }
    }

    if ($value -match '(?i)cannot overwrite non-directory.+artifacts\.json.+with directory') {
        return [pscustomobject]@{
            Code = 'LEGACY_INSTALLER_DESTINATION'
            Title = 'Wybrany folder zawiera inną instalację'
            Message = 'Stary install.ps1 próbuje skopiować paczkę na istniejący plik lub do niezgodnego układu katalogów.'
            Remedy = 'Nie uruchamiaj starego install.ps1 na folderze obecnej paczki All-in-One. Rozpakuj pełną paczkę do pustego folderu i uruchom Metin2-Launcher-GUI.bat. Istniejącej bazy Dockera nie usuwaj.'
        }
    }

    # Docker Desktop's own Linux disk went read-only or ran out of room, so the
    # image could not be written. Nothing of the server is touched; the fix is
    # a clean restart of the WSL machine and free space - never Docker's
    # "Clean / Purge data", which takes the database with it.
    if ($value -match '(?i)read-only file system|no space left on device|desktop-containerd.+(?:input/output error|meta\.db)') {
        return [pscustomobject]@{
            Code = 'DOCKER_DISK_BROKEN'
            Title = 'Dysk maszyny Dockera jest tylko do odczytu albo pełny'
            Message = 'Docker nie mógł zapisać obrazu na swoim dysku WSL (komunikat „read-only file system” albo „no space left on device”). Pliki serwera i baza są w porządku; to stan maszyny wirtualnej Docker Desktop po nieczystym zamknięciu lub braku miejsca.'
            Remedy = 'Zamknij Docker Desktop (ikona w zasobniku → Quit), w PowerShell wykonaj: wsl --shutdown, sprawdź wolne miejsce na dysku z folderem %LOCALAPPDATA%\Docker\wsl (potrzeba kilku GB), uruchom Docker Desktop ponownie i kliknij GRAJ. Nie używaj w Docker Desktop opcji „Clean / Purge data” ani „Reset to factory defaults” - usuwają bazę z postaciami.'
        }
    }
    if ($value -match "(?i)playerbot-migrate.+didn.t complete successfully|database import was not ready after|user: 'unauthenticated'") {
        return [pscustomobject]@{
            Code = 'DB_USER_BROKEN'
            Title = 'Serwer nie może zalogować się do własnej bazy'
            Message = 'Baza działa, ale techniczne konto, którym łączy się serwer, nie jest rozpoznawane. Dlatego krok „playerbot-migrate” nie kończy się poprawnie, a gra i panel nie wstają. Twoje postacie, przedmioty i boty są bezpieczne.'
            Remedy = 'W launcherze kliknij „NAPRAW DOSTĘP DO BAZY”, poczekaj na komunikat „Gotowe”, a potem kliknij „GRAJ”. Nie usuwaj wolumenów i nie używaj docker compose down -v.'
        }
    }

    if ($value -match '(?i)\b404\b|not found.+update-manifest|update-manifest.+not found') {
        return [pscustomobject]@{
            Code = 'UPDATE_CHANNEL_UNPUBLISHED'
            Title = 'Kanał aktualizacji nie został jeszcze opublikowany'
            Message = 'Serwer GitHub nie ma obecnie manifestu aktualizacji. Nie oznacza to uszkodzenia zainstalowanego serwera.'
            Remedy = 'Możesz nadal grać na obecnej wersji. Spróbuj ponownie później; launcher nie powinien niczego instalować ani tworzyć drugiego serwera.'
        }
    }

    return [pscustomobject]@{
        Code = 'UNKNOWN'
        Title = 'Operacja nie powiodła się'
        Message = if ($value) { ($value -split '\r?\n' | Select-Object -Last 1) } else { 'Nie otrzymano szczegółów błędu.' }
        Remedy = 'Uruchom „Diagnostyka”, następnie „Zbierz logi (ZIP)” i prześlij utworzony plik na kanał pomocy projektu.'
    }
}

function Get-M2InstallationProjectName {
    param([Parameter(Mandatory = $true)][string]$ServerRoot)

    $statePath = Join-Path $ServerRoot '.m2install.json'
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$state.projectName) { return [string]$state.projectName }
        }
        catch {}
    }

    $envPath = Join-Path $ServerRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = Select-String -LiteralPath $envPath -Pattern '^M2_COMPOSE_PROJECT_NAME=(.+)$' | Select-Object -First 1
        if ($match -and $match.Matches[0].Groups[1].Value) {
            return $match.Matches[0].Groups[1].Value.Trim()
        }
    }
    return ''
}

function Get-M2PanelPort {
    param([Parameter(Mandatory = $true)][string]$ServerRoot)

    $envPath = Join-Path $ServerRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = Select-String -LiteralPath $envPath -Pattern '^M2_PANEL_PUBLIC_PORT=(\d+)$' | Select-Object -First 1
        if ($match) { return [int]$match.Matches[0].Groups[1].Value }
    }
    return 7788
}

function Get-M2ListeningProcess {
    param([Parameter(Mandatory = $true)][int]$Port)

    try {
        $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop | Select-Object -First 1
        if (-not $connection) { return $null }
        $processName = ''
        try { $processName = (Get-Process -Id $connection.OwningProcess -ErrorAction Stop).ProcessName } catch {}
        return [pscustomobject]@{ Pid = [int]$connection.OwningProcess; Name = $processName }
    }
    catch {
        $netstat = Invoke-M2DiagnosticProcess -FileName 'netstat.exe' -Arguments '-ano -p tcp' -TimeoutMilliseconds 3000
        if ($netstat.ExitCode -ne 0) { return $null }
        foreach ($line in ($netstat.Output -split '\r?\n')) {
            if ($line -match ('(?i)^\s*TCP\s+\S+:' + $Port + '\s+\S+\s+LISTENING\s+(\d+)\s*$')) {
                $pidValue = [int]$Matches[1]
                $processName = ''
                try { $processName = (Get-Process -Id $pidValue -ErrorAction Stop).ProcessName } catch {}
                return [pscustomobject]@{ Pid = $pidValue; Name = $processName }
            }
        }
    }
    return $null
}

function Get-M2DockerPortOwner {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [AllowEmptyString()][string]$CurrentProject = ''
    )

    $dockerPs = Invoke-M2DiagnosticProcess -FileName 'docker.exe' -Arguments 'ps --format "{{json .}}"' -TimeoutMilliseconds 4000
    if ($dockerPs.ExitCode -ne 0) { return $null }
    foreach ($line in ($dockerPs.Output -split '\r?\n')) {
        if (-not $line.Trim()) { continue }
        try { $container = $line | ConvertFrom-Json } catch { continue }
        $ports = [string]$container.Ports
        if ($ports -notmatch ('(?i)(?:^|,\s*)(?:(?:0\.0\.0\.0|127\.0\.0\.1|\[::\]|\*):)?' + $Port + '->')) { continue }
        $project = ''
        $labels = [string]$container.Labels
        if ($labels -match '(?:^|,)com\.docker\.compose\.project=([^,]+)') { $project = $Matches[1] }
        return [pscustomobject]@{
            Container = [string]$container.Names
            Project = $project
            IsCurrentProject = [bool]($CurrentProject -and $project -and $project.Equals($CurrentProject, [StringComparison]::OrdinalIgnoreCase))
        }
    }
    return $null
}

# The TCP ranges Windows has reserved for itself (Hyper-V, WSL, NAT). A port
# inside one cannot be bound by anything, Docker included, and the failure
# only shows up a second after the images are built. Empty when netsh is
# missing or says nothing - never a reason to refuse a start on its own.
function Get-M2ExcludedPortRanges {
    $ranges = @()
    try {
        $lines = & netsh interface ipv4 show excludedportrange protocol=tcp 2>$null
        foreach ($line in @($lines)) {
            if ("$line" -match '^\s*(\d+)\s+(\d+)\s*\*?\s*$') {
                $ranges += [pscustomobject]@{ Start = [int]$Matches[1]; End = [int]$Matches[2] }
            }
        }
    }
    catch { }
    return $ranges
}

function Get-M2ExcludedPortHit {
    param([Parameter(Mandatory = $true)][int]$Port, [object[]]$Ranges)
    foreach ($r in @($Ranges)) {
        if ($Port -ge $r.Start -and $Port -le $r.End) { return $r }
    }
    return $null
}

function Get-DockerDesktopCandidates {
    # The three stock folders, then wherever the CLI on PATH lives (Docker
    # Desktop keeps docker.exe under <install>\resources\bin), then the
    # uninstall entry's InstallLocation. Two players had Docker on another
    # drive: the launcher stopped Docker Desktop for them and then could not
    # start it again, and the update that happened to come between the two
    # got the blame.
    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($p in @(
            (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
            (Join-Path ${env:ProgramFiles(x86)} 'Docker\Docker\Docker Desktop.exe'),
            (Join-Path $env:LOCALAPPDATA 'Docker\Docker Desktop.exe'))) {
        if ($p) { $paths.Add($p) }
    }
    try {
        $cli = (Get-Command docker -ErrorAction Stop).Source
        if ($cli) {
            $root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $cli))
            if ($root) { $paths.Add((Join-Path $root 'Docker Desktop.exe')) }
        }
    }
    catch { }
    foreach ($key in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop',
                       'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop')) {
        try {
            $loc = (Get-ItemProperty -LiteralPath $key -ErrorAction Stop).InstallLocation
            if ($loc) { $paths.Add((Join-Path $loc 'Docker Desktop.exe')) }
        }
        catch { }
    }
    return @($paths | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique)
}

function Get-M2DockerPreflight {
    param(
        [Parameter(Mandatory = $true)][string]$ServerRoot,
        [switch]$CheckPanelPort
    )

    $root = [IO.Path]::GetFullPath($ServerRoot)
    $checks = [Collections.ArrayList]::new()
    $blocking = [Collections.ArrayList]::new()
    $warnings = [Collections.ArrayList]::new()
    $dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    $dockerCliPresent = $null -ne $dockerCommand
    $dockerProcessesRunning = @(Get-Process -Name 'Docker Desktop', 'com.docker.backend' -ErrorAction SilentlyContinue).Count -gt 0
    $dockerEngineReady = $false

    if ($dockerCliPresent) {
        [void]$checks.Add('OK: Docker CLI jest zainstalowany.')
        $dockerProbe = Invoke-M2DiagnosticProcess -FileName 'docker.exe' -Arguments 'info --format "{{.ServerVersion}}"' -TimeoutMilliseconds 3500
        $dockerProbeText = if ($null -ne $dockerProbe.Output) { $dockerProbe.Output.Trim() } else { '' }
        # `docker info` exits 0 and still prints the daemon's own refusal. "Error
        # response from daemon: Docker Desktop is unable to start" arrives on
        # stderr, where the server version should be, and the exit code says
        # nothing is wrong - so the check reported "OK: Docker Engine odpowiada
        # (wersja Error response from daemon: Docker Desktop is unable to start)"
        # and a verdict of "mozna uruchomic serwer", six times over, to a player
        # whose WSL was broken. He therefore never saw the one warning that names
        # what to repair, because that warning is only raised when the engine is
        # known to be down. A version is digits and dots; anything else is the
        # engine failing to answer.
        $dockerVersion = ''
        foreach ($probeLine in ($dockerProbeText -split "`r?`n")) {
            $candidate = $probeLine.Trim()
            if ($candidate -match '^\d+(\.\d+)+') {
                $dockerVersion = $candidate
                break
            }
        }
        $dockerEngineReady = $dockerProbe.ExitCode -eq 0 -and -not $dockerProbe.TimedOut -and $dockerVersion -ne ''
        if ($dockerEngineReady) {
            [void]$checks.Add("OK: Docker Engine odpowiada (wersja $dockerVersion).")
        }
        elseif ($dockerProbeText -and -not $dockerProbe.TimedOut) {
            # What the daemon said, not a tidy summary of it: the message names
            # the fault and the player pastes it straight into a report.
            [void]$checks.Add("BLAD: Docker Engine nie odpowiada: $dockerProbeText")
            [void]$warnings.Add("Silnik Dockera nie wystartowal: $dockerProbeText")
        }
        elseif ($dockerProcessesRunning) {
            [void]$checks.Add('UWAGA: Docker Desktop jest otwarty, ale Engine jeszcze nie odpowiada.')
            [void]$warnings.Add('Docker Desktop nadal startuje albo zatrzymał się na błędzie.')
        }
        else {
            [void]$checks.Add('INFO: Docker Engine jest zatrzymany; launcher może go uruchomić.')
        }
    }
    else {
        [void]$checks.Add('BŁĄD: nie znaleziono Docker CLI.')
        [void]$blocking.Add('Zainstaluj Docker Desktop z oficjalnej strony i uruchom ponownie launcher.')
    }

    $desktopCandidates = @(Get-DockerDesktopCandidates)
    if (-not $dockerEngineReady -and $desktopCandidates.Count -eq 0) {
        [void]$blocking.Add('Nie znaleziono programu Docker Desktop. Zainstaluj go przed uruchomieniem serwera.')
    }

    $virtualization = 'Unknown'
    try {
        $computer = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
        $processor = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop | Select-Object -First 1
        if ([bool]$computer.HypervisorPresent -or [bool]$processor.VirtualizationFirmwareEnabled) {
            $virtualization = 'Enabled'
            [void]$checks.Add('OK: wirtualizacja procesora jest dostępna.')
        }
        elseif ($null -ne $processor.VirtualizationFirmwareEnabled) {
            $virtualization = 'Disabled'
            [void]$checks.Add('BŁĄD: wirtualizacja procesora jest wyłączona w BIOS/UEFI.')
            if (-not $dockerEngineReady) {
                [void]$blocking.Add('Włącz AMD SVM/AMD-V albo Intel VT-x w BIOS/UEFI, a następnie zrestartuj komputer.')
            }
        }
    }
    catch {
        [void]$checks.Add('INFO: Windows nie udostępnił stanu wirtualizacji; Docker zweryfikuje go przy starcie.')
    }

    $wslState = 'Missing'
    $wslCommand = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if ($wslCommand) {
        $wslProbe = Invoke-M2DiagnosticProcess -FileName 'wsl.exe' -Arguments '--status' -TimeoutMilliseconds 4500
        if ($wslProbe.ExitCode -eq 0) {
            $wslState = 'Ready'
            [void]$checks.Add('OK: WSL odpowiada.')
        }
        else {
            $wslState = 'Error'
            [void]$checks.Add('UWAGA: polecenie wsl --status nie działa poprawnie.')
            if (-not $dockerEngineReady) {
                [void]$warnings.Add('Jeżeli Docker nie wystartuje, uruchom PowerShell jako administrator, wykonaj wsl --update i wsl --install, a następnie zrestartuj Windows.')
            }
        }
    }
    else {
        [void]$checks.Add('UWAGA: Windows Subsystem for Linux nie jest zainstalowany lub nie jest widoczny.')
        if (-not $dockerEngineReady) {
            [void]$warnings.Add('Docker Desktop zwykle wymaga WSL 2. W razie błędu wykonaj jako administrator: wsl --install, a potem zrestartuj Windows.')
        }
    }

    $panelPort = Get-M2PanelPort -ServerRoot $root
    $portOwner = $null
    $dockerPortOwner = $null
    $currentProject = Get-M2InstallationProjectName -ServerRoot $root
    if ($CheckPanelPort) {
        $portOwner = Get-M2ListeningProcess -Port $panelPort
        if ($portOwner) {
            if ($dockerEngineReady) {
                $dockerPortOwner = Get-M2DockerPortOwner -Port $panelPort -CurrentProject $currentProject
            }
            if ($dockerPortOwner -and $dockerPortOwner.IsCurrentProject) {
                [void]$checks.Add("OK: port panelu $panelPort należy do tej instalacji ($($dockerPortOwner.Container)).")
            }
            else {
                $ownerText = if ($dockerPortOwner) {
                    "kontener $($dockerPortOwner.Container), projekt $($dockerPortOwner.Project)"
                }
                elseif ($portOwner.Name) { "proces $($portOwner.Name), PID $($portOwner.Pid)" }
                else { "PID $($portOwner.Pid)" }
                [void]$checks.Add("BŁĄD: port panelu $panelPort jest zajęty przez $ownerText.")
                [void]$blocking.Add("Port $panelPort zajmuje inna aplikacja lub instalacja. Zatrzymaj poprzedni serwer albo uruchamiaj go z jego własnego folderu launchera.")
            }
        }
        else {
            [void]$checks.Add("OK: port panelu $panelPort jest wolny.")
        }
    }

    # Ports the stack binds on the host, against the ranges Windows reserved.
    # The game ports are the ones that fail in practice: a range that starts
    # at 11000 or 13000 blocks the login server or the channel, and nothing
    # in the launcher used to say so.
    # @(): a function's array of one unrolls to a bare object and of none to
    # $null, and under StrictMode neither has .Count - every player whose
    # Windows reserved exactly one port range (or none) got "The property
    # 'Count' cannot be found on this object" from Start, StartDocker and
    # Logs alike, because all three run this preflight.
    $excludedRanges = @(Get-M2ExcludedPortRanges)
    if ($excludedRanges.Count -gt 0) {
        $envPath = Join-Path $root 'linux-port\docker\.env'
        $authPort = 11000
        $dbPort = 3306
        if (Test-Path -LiteralPath $envPath -PathType Leaf) {
            $m = Select-String -LiteralPath $envPath -Pattern '^M2_AUTH_PORT=(\d+)$' | Select-Object -First 1
            if ($m) { $authPort = [int]$m.Matches[0].Groups[1].Value }
            $m = Select-String -LiteralPath $envPath -Pattern '^M2_DB_PUBLISH_PORT=(\d+)$' | Select-Object -First 1
            if ($m) { $dbPort = [int]$m.Matches[0].Groups[1].Value }
        }
        $stackPorts = @(
            @{ Port = $authPort; Name = 'serwer logowania' },
            @{ Port = 13000; Name = 'kanal gry' },
            @{ Port = 13001; Name = 'kanal gry' },
            @{ Port = 13002; Name = 'kanal gry' },
            @{ Port = $dbPort; Name = 'baza danych' },
            @{ Port = [int]$panelPort; Name = 'panel' }
        )
        $hits = @()
        foreach ($p in $stackPorts) {
            $hit = Get-M2ExcludedPortHit -Port $p.Port -Ranges $excludedRanges
            if ($hit) { $hits += "$($p.Port) ($($p.Name), zakres $($hit.Start)-$($hit.End))" }
        }
        if ($hits.Count -gt 0) {
            [void]$checks.Add("BŁĄD: Windows zarezerwował porty serwera: $($hits -join ', ').")
            [void]$blocking.Add('Port serwera leży w zakresie zarezerwowanym przez Windows (Hyper-V/WSL), więc Docker nie może na nim nasłuchiwać. Uruchom PowerShell jako administrator: net stop winnat, kliknij GRAJ, a po starcie serwera: net start winnat. Zwykle pomaga też restart Windows.')
        }
        else {
            [void]$checks.Add('OK: żaden port serwera nie leży w zakresie zarezerwowanym przez Windows.')
        }
    }

    return [pscustomobject]@{
        CanStart = $blocking.Count -eq 0
        DockerCliPresent = $dockerCliPresent
        DockerProcessesRunning = $dockerProcessesRunning
        DockerEngineReady = $dockerEngineReady
        Virtualization = $virtualization
        Wsl = $wslState
        PanelPort = $panelPort
        CurrentProject = $currentProject
        Checks = @($checks)
        Warnings = @($warnings)
        BlockingIssues = @($blocking)
    }
}

function Format-M2DockerPreflightReport {
    param([Parameter(Mandatory = $true)]$Report)

    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('=== DIAGNOSTYKA METIN2 PLAYERBOTS ===')
    foreach ($check in @($Report.Checks)) { $lines.Add([string]$check) }
    if (@($Report.Warnings).Count -gt 0) {
        $lines.Add('')
        $lines.Add('Ostrzeżenia:')
        foreach ($warning in @($Report.Warnings)) { $lines.Add("- $warning") }
    }
    if (@($Report.BlockingIssues).Count -gt 0) {
        $lines.Add('')
        $lines.Add('Co trzeba zrobić:')
        foreach ($issue in @($Report.BlockingIssues)) { $lines.Add("- $issue") }
    }
    $lines.Add('')
    $lines.Add('Wynik: ' + $(if ($Report.CanStart) { 'można uruchomić serwer.' } else { 'najpierw usuń powyższy problem.' }))
    return $lines -join [Environment]::NewLine
}

Export-ModuleMember -Function @(
    'Get-M2LauncherErrorGuidance',
    'Get-M2DockerPreflight',
    'Format-M2DockerPreflightReport'
)
