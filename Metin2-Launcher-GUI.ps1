[CmdletBinding()]
param([switch]$SelfTest)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$cliLauncher = Join-Path $root 'Metin2-Launcher.ps1'
$modulePath = Join-Path $root 'launcher\Metin2Launcher.psm1'
$diagnosticsModulePath = Join-Path $root 'launcher\Metin2Launcher.Diagnostics.psm1'
$configPath = Join-Path $root '.m2launcher.json'
$logDirectory = Join-Path $root 'launcher-logs'
$supportDirectory = Join-Path $root 'support-bundles'
$composeFile = Join-Path $root 'linux-port\docker\docker-compose.yml'
$sessionLog = Join-Path $logDirectory ('launcher-{0}.log' -f (Get-Date -Format 'yyyyMMdd'))

function Write-StartupFailure {
    # Straight to the file: this runs before (or instead of) the window, so
    # Write-LocalLog and its on-screen box may not exist yet.
    param([string]$Text)
    try {
        New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
        [IO.File]::AppendAllText($sessionLog,
            ('{0}  BLAD LAUNCHERA: {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Text) + [Environment]::NewLine,
            [Text.UTF8Encoding]::new($false))
    }
    catch { }
}

trap {
    # A launcher that dies before its first log line left nothing behind but a
    # dialog nobody could copy from - after the 2.0.8 restart the session log
    # ended at "Uruchamiam launcher ponownie" and the player saw an error box
    # (11 September). Whatever stops the script is written down first, then
    # shown with its text, so the next report carries the reason.
    Write-StartupFailure ($_ | Out-String)
    try {
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.MessageBox]::Show(
            ("Launcher nie wystartowal:`r`n`r`n{0}`r`n`r`nSzczegoly sa w folderze launcher-logs." -f $_.Exception.Message),
            'Blad launchera', 'OK', 'Error') | Out-Null
    }
    catch { }
    break
}

foreach ($required in @($cliLauncher, $modulePath, $diagnosticsModulePath, $composeFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Brakuje wymaganego pliku: $required"
    }
}

Import-Module $modulePath -Force
Import-Module $diagnosticsModulePath -Force
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic
# Before the first control exists: an exception thrown inside a button or
# timer handler is logged with its stack and shown with its text, instead of
# the .NET "Unhandled exception has occurred" dialog and an empty log.
[Windows.Forms.Application]::SetUnhandledExceptionMode([Windows.Forms.UnhandledExceptionMode]::CatchException)
[Windows.Forms.Application]::add_ThreadException([System.Threading.ThreadExceptionEventHandler]{
    param($sender, $eventArgs)
    Write-StartupFailure ('w oknie: ' + $eventArgs.Exception.ToString())
    try {
        [Windows.Forms.MessageBox]::Show(
            ("Blad w oknie launchera:`r`n`r`n{0}`r`n`r`nSzczegoly sa w folderze launcher-logs. Okno dziala dalej." -f $eventArgs.Exception.Message),
            'Blad launchera', 'OK', 'Error') | Out-Null
    }
    catch { }
})

if ($SelfTest) {
    $cliErrors = $null
    $guiErrors = $null
    $diagnosticErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($cliLauncher, [ref]$null, [ref]$cliErrors)
    [void][System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath, [ref]$null, [ref]$guiErrors)
    [void][System.Management.Automation.Language.Parser]::ParseFile($diagnosticsModulePath, [ref]$null, [ref]$diagnosticErrors)
    $formProbe = [Windows.Forms.Form]::new()
    $formProbe.Dispose()
    $portGuidance = Get-M2LauncherErrorGuidance -Text 'Bind for 127.0.0.1:7788 failed: port is already allocated'
    $wslGuidance = Get-M2LauncherErrorGuidance -Text 'There was a problem with WSL; wsl.exe exit status 1'
    [pscustomobject]@{
        Gui = 'OK'
        CliParserErrors = @($cliErrors).Count
        GuiParserErrors = @($guiErrors).Count
        DiagnosticsParserErrors = @($diagnosticErrors).Count
        PortErrorParser = $portGuidance.Code
        WslErrorParser = $wslGuidance.Code
        ComposePresent = Test-Path -LiteralPath $composeFile -PathType Leaf
        DockerCliPresent = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
        ConfigReadable = $null -ne (Get-M2LauncherConfig -ServerRoot $root -ConfigPath $configPath)
    } | ConvertTo-Json
    exit 0
}

[Windows.Forms.Application]::EnableVisualStyles()

# The session log is opened in Notepad and pasted into chat, and Polish letters
# do not survive either. Everything written to the file is transliterated; the
# on-screen box is left alone, because it renders them correctly and there is no
# reason to make the window worse to fix the file. A character that is neither
# ASCII nor in the table - including the replacement character left behind by an
# older, mis-encoded log - becomes a question mark rather than disappearing.
$script:M2_ASCII_MAP = @{
    [char]0x0105 = 'a'; [char]0x0107 = 'c'; [char]0x0119 = 'e'; [char]0x0142 = 'l'
    [char]0x0144 = 'n'; [char]0x00F3 = 'o'; [char]0x015B = 's'; [char]0x017A = 'z'
    [char]0x017C = 'z'
    [char]0x0104 = 'A'; [char]0x0106 = 'C'; [char]0x0118 = 'E'; [char]0x0141 = 'L'
    [char]0x0143 = 'N'; [char]0x00D3 = 'O'; [char]0x015A = 'S'; [char]0x0179 = 'Z'
    [char]0x017B = 'Z'
    [char]0x2013 = '-'; [char]0x2014 = '-'; [char]0x2026 = '...'
    [char]0x2018 = "'"; [char]0x2019 = "'"; [char]0x201C = '"'; [char]0x201D = '"'
    [char]0x00A0 = ' '
}

function ConvertTo-M2AsciiLine {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    $builder = New-Object Text.StringBuilder
    foreach ($ch in $Text.ToCharArray()) {
        if ($script:M2_ASCII_MAP.ContainsKey($ch)) {
            [void]$builder.Append($script:M2_ASCII_MAP[$ch])
        }
        elseif ([int]$ch -lt 128) { [void]$builder.Append($ch) }
        else { [void]$builder.Append('?') }
    }
    return $builder.ToString()
}

function Write-LocalLog {
    # -FileOnly keeps very chatty build output (apt, unpacking) in the session
    # log without flooding the small on-screen box.
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [switch]$FileOnly
    )
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    [IO.File]::AppendAllText($sessionLog,
        (ConvertTo-M2AsciiLine $line) + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false))
    if (-not $FileOnly -and $script:logBox -and -not $script:logBox.IsDisposed) {
        $script:logBox.AppendText($line + [Environment]::NewLine)
        # Keep the box bounded so a long build cannot grow it without limit.
        if ($script:logBox.Lines.Count -gt 600) {
            $script:logBox.Lines = $script:logBox.Lines[-400..-1]
        }
        $script:logBox.SelectionStart = $script:logBox.TextLength
        $script:logBox.ScrollToCaret()
    }
}

function New-Button {
    param(
        [string]$Text,
        [int]$X,
        [int]$Y,
        [int]$Width = 210,
        [int]$Height = 52,
        [Drawing.Color]$Color = [Drawing.Color]::FromArgb(45, 110, 190)
    )
    $button = [Windows.Forms.Button]::new()
    $button.Text = $Text
    $button.Location = [Drawing.Point]::new($X, $Y)
    $button.Size = [Drawing.Size]::new($Width, $Height)
    $button.BackColor = $Color
    $button.ForeColor = [Drawing.Color]::White
    $button.FlatStyle = 'Flat'
    $button.FlatAppearance.BorderSize = 0
    $button.Font = [Drawing.Font]::new('Segoe UI Semibold', 10)
    $button.Cursor = [Windows.Forms.Cursors]::Hand
    return $button
}

function Get-LauncherConfig {
    Get-M2LauncherConfig -ServerRoot $root -ConfigPath $configPath
}

# Every word this window shows, in both languages.
#
# The Discord has more and more English speakers and a launcher they cannot read
# is a launcher they run wrongly - the difference between "ZATRZYMAJ I ZAPISZ"
# and "wipe everything" is not guessable. Only the interface is translated here;
# the two web panels are separate applications with their own thousand-odd
# strings and are not covered by this switch.
$script:Strings = @{
    pl = @{
        formTitle    = 'Metin2 Singleplayer Playerbots - All in One'
        title        = 'METIN2 SINGLEPLAYER - PLAYERBOTS'
        subtitle     = 'Prosty launcher: Docker, serwer, klient, aktualizacje i diagnostyka w jednym miejscu.'
        install      = '1. ZAINSTALUJ / PRZYGOTUJ'
        play         = '2. GRAJ (SERWER + KLIENT)'
        docker       = 'URUCHOM DOCKER'
        stop         = 'ZATRZYMAJ I ZAPISZ'
        panel        = 'OTWORZ PANEL WWW'
        client       = 'WYBIERZ KLIENTA'
        update       = 'SPRAWDZ AKTUALIZACJE'
        bundle       = 'ZBIERZ / WYSLIJ LOGI'
        diagnostics  = 'DIAGNOSTYKA'
        openLog      = 'OTWORZ LOG'
        logFolder    = 'FOLDER LOGOW'
        botCount     = 'LICZBA BOTOW (0-2500)'
        importDb     = 'IMPORTUJ BAZE'
        worldBackup  = 'KOPIA SWIATA'
        backupDialog = 'Kopia swiata'
        backupInfo   = 'Kopia zapisuje caly swiat - postacie, poziomy, ekwipunek, boty i konta gry - do jednego pliku zip w folderze backups. Serwer zostanie na czas kazdej z tych operacji zatrzymany i zapisany.'
        backupMake   = 'Zapisz kopie swiata'
        backupLoad   = 'Przywroc swiat z kopii'
        backupReset  = 'Zacznij od zera (swieza instalacja)'
        backupPick   = 'Wybierz plik kopii'
        backupNone   = 'W folderze backups nie ma jeszcze zadnej kopii. Zapisz najpierw kopie.'
        repairDb     = 'NAPRAW DOSTEP DO BAZY'
        dbAccess     = 'DANE DO BAZY (NAVICAT)'
        gmPanel      = 'PANEL GM F9 (TEST)'
        updateClient = 'AKTUALIZUJ KLIENTA'
        dbAccessTitle = 'Dane do polaczenia z baza'
        dbAccessHint = 'Wpisz te dane w Navicat, HeidiSQL albo DBeaver (typ MySQL/MariaDB, polaczenie TCP). Konto root widzi wszystko, konto gry tylko bazy gry. Baza slucha wylacznie na tym komputerze. Jesli baza odrzuca haslo, kliknij NAPRAW DOSTEP DO BAZY - ustawia oba konta na hasla z pliku .env. Nie wklejaj tych hasel na Discordzie.'
        dbAccessProtoNote = 'Na plikach 2.x przedmioty i potwory (item_proto, mob_proto) sa w bazie world; player.item_proto i player.mob_proto to tylko widoki. Zmiany w world zostaja po restarcie serwera.'
        startupUpdateTitle = 'Dostepna aktualizacja'
        startupServerUpdate = 'Znaleziono nowsza wersje serwera: {0}' + [Environment]::NewLine + '(zainstalowana: {1})' + [Environment]::NewLine + [Environment]::NewLine + 'Czy chcesz dokonac aktualizacji teraz?' + [Environment]::NewLine + [Environment]::NewLine + 'Postacie, przedmioty i boty zostana bez zmian. Serwer zostanie przebudowany - postep w logu na dole. Odpowiedz NIE odklada pytanie do nastepnej wersji; przycisk AKTUALIZUJ dziala zawsze.'
        startupClientUpdate = 'Znaleziono nowsza wersje klienta: {0}' + [Environment]::NewLine + '(zainstalowana: {1})' + [Environment]::NewLine + [Environment]::NewLine + 'Czy chcesz zaktualizowac klienta teraz?' + [Environment]::NewLine + [Environment]::NewLine + 'Podmienia pliki pack w folderze klienta; poprzednie trafiaja do backups\client. Odpowiedz NIE odklada pytanie do nastepnej wersji; przycisk AKTUALIZUJ KLIENTA dziala zawsze.'
        dbAccessOpenEnv = 'OTWORZ PLIK .ENV'
        dbAccessNoEnv = 'Brak pliku linux-port\docker\.env - uruchom najpierw serwer (GRAJ), launcher go utworzy.'
        language     = 'JEZYK: POLSKI'
        ready        = 'Gotowy.'
        footer       = '"Zatrzymaj i zapisz" nie usuwa postaci ani postepu botow. Nigdy nie uzywa docker compose down -v.'
        botDialog    = 'Liczba grajacych botow'
        apply        = 'Zastosuj'
        cancel       = 'Anuluj'
        panelDialog  = 'Ktory panel otworzyc?'
        panelInfo    = 'Oba panele pokazuja ten sam swiat i dzialaja jednoczesnie.'
        panelClassic = "Oryginalny panel`r`nmapa i sterowanie"
        panelSeban   = "Zaawansowany panel seban latino`r`nprofile, rankingi, gospodarka, obciazenie"
        panelPw      = 'Nie moge sie zalogowac (haslo do panelu)'
        importDialog = 'Importuj baze z innej instalacji'
        importInfo   = 'Wybierz zrodlowa instalacje. Jej swiat (postacie, poziomy, ekwipunek) zostanie skopiowany do biezacej instalacji.'
        importOk     = 'Importuj'
        langSwitched = 'Jezyk zmieniony. Uruchom launcher ponownie, zeby zobaczyc zmiane.'
    }
    en = @{
        formTitle    = 'Metin2 Singleplayer Playerbots - All in One'
        title        = 'METIN2 SINGLEPLAYER - PLAYERBOTS'
        subtitle     = 'One launcher: Docker, the server, the client, updates and diagnostics in one place.'
        install      = '1. INSTALL / PREPARE'
        play         = '2. PLAY (SERVER + CLIENT)'
        docker       = 'START DOCKER'
        stop         = 'STOP AND SAVE'
        panel        = 'OPEN WEB PANEL'
        client       = 'CHOOSE CLIENT'
        update       = 'CHECK FOR UPDATES'
        bundle       = 'COLLECT / SEND LOGS'
        diagnostics  = 'DIAGNOSTICS'
        openLog      = 'OPEN LOG'
        logFolder    = 'LOG FOLDER'
        botCount     = 'BOT COUNT (0-2500)'
        importDb     = 'IMPORT DATABASE'
        worldBackup  = 'WORLD BACKUP'
        backupDialog = 'World backup'
        backupInfo   = 'A backup writes the whole world - characters, levels, equipment, bots and game accounts - into one zip file in the backups folder. The server is stopped and saved for each of these operations.'
        backupMake   = 'Save a backup'
        backupLoad   = 'Restore from a backup'
        backupReset  = 'Start over (fresh install)'
        backupPick   = 'Choose a backup file'
        backupNone   = 'There is no backup in the backups folder yet. Save one first.'
        repairDb     = 'REPAIR DATABASE ACCESS'
        dbAccess     = 'DATABASE LOGIN (NAVICAT)'
        gmPanel      = 'GM PANEL F9 (BETA)'
        updateClient = 'UPDATE CLIENT'
        dbAccessTitle = 'Database connection details'
        dbAccessHint = 'Enter these in Navicat, HeidiSQL or DBeaver (MySQL/MariaDB, TCP connection). root sees everything, the game account only the game databases. The database listens on this computer only. If it rejects the password, click REPAIR DATABASE ACCESS - it sets both accounts to the passwords in .env. Never paste these passwords on Discord.'
        dbAccessProtoNote = 'On the 2.x files items and monsters (item_proto, mob_proto) live in the world database; player.item_proto and player.mob_proto are views. Changes in world survive a server restart.'
        startupUpdateTitle = 'Update available'
        startupServerUpdate = 'A newer server version was found: {0}' + [Environment]::NewLine + '(installed: {1})' + [Environment]::NewLine + [Environment]::NewLine + 'Update now?' + [Environment]::NewLine + [Environment]::NewLine + 'Characters, items and bots stay as they are. The server is rebuilt - progress in the log below. NO postpones the question until the next version; the UPDATE button always works.'
        startupClientUpdate = 'A newer client version was found: {0}' + [Environment]::NewLine + '(installed: {1})' + [Environment]::NewLine + [Environment]::NewLine + 'Update the client now?' + [Environment]::NewLine + [Environment]::NewLine + 'Replaces the pack files in the client folder; the previous ones go to backups\client. NO postpones the question until the next version; the UPDATE CLIENT button always works.'
        dbAccessOpenEnv = 'OPEN .ENV FILE'
        dbAccessNoEnv = 'No linux-port\docker\.env yet - start the server (PLAY) once, the launcher creates it.'
        language     = 'LANGUAGE: ENGLISH'
        ready        = 'Ready.'
        footer       = '"Stop and save" never deletes characters or bot progress. It never uses docker compose down -v.'
        botDialog    = 'Number of playing bots'
        apply        = 'Apply'
        cancel       = 'Cancel'
        panelDialog  = 'Which panel should open?'
        panelInfo    = 'Both panels show the same world and run at the same time.'
        panelClassic = "Original panel`r`nmap and controls"
        panelSeban   = "Advanced panel by seban latino`r`nprofiles, rankings, economy, load"
        panelPw      = 'I cannot log in (panel password)'
        importDialog = 'Import a database from another installation'
        importInfo   = 'Pick the source installation. Its world - characters, levels, equipment - is copied into this one.'
        importOk     = 'Import'
        langSwitched = 'Language changed. Restart the launcher to see it.'
    }
}

$script:Lang = 'pl'
try {
    $storedLang = (Get-LauncherConfig).language
    if ($storedLang -eq 'en') { $script:Lang = 'en' }
}
catch { }

function T {
    param([Parameter(Mandatory = $true)][string]$Key)
    $table = $script:Strings[$script:Lang]
    if ($table -and $table.ContainsKey($Key)) { return [string]$table[$Key] }
    return [string]$script:Strings['pl'][$Key]
}

function Switch-LauncherLanguage {
    $config = Get-LauncherConfig
    $config.language = if ($script:Lang -eq 'en') { 'pl' } else { 'en' }
    Save-M2LauncherConfig -Config $config -ConfigPath $configPath
    $script:Lang = $config.language
    Write-LocalLog ("Language: {0}" -f $config.language)
    [Windows.Forms.MessageBox]::Show((T 'langSwitched'), (T 'formTitle'),
        [Windows.Forms.MessageBoxButtons]::OK,
        [Windows.Forms.MessageBoxIcon]::Information) | Out-Null
}

function Save-ClientExecutable {
    param([Parameter(Mandatory = $true)][string]$Executable)
    $config = Get-LauncherConfig
    $config.clientExecutable = [IO.Path]::GetFullPath($Executable)
    $config.clientRoot = [IO.Path]::GetFullPath((Split-Path -Parent $Executable))
    Save-M2LauncherConfig -Config $config -ConfigPath $configPath
    Write-LocalLog "Wybrano klienta: $([IO.Path]::GetFileName($Executable))"
}

function Select-ClientExecutable {
    $config = Get-LauncherConfig
    $dialog = [Windows.Forms.OpenFileDialog]::new()
    $dialog.Title = 'Wybierz plik uruchamiający klienta Metin2'
    $dialog.Filter = 'Program klienta Metin2 (*.exe)|*.exe|Wszystkie pliki (*.*)|*.*'
    $dialog.CheckFileExists = $true
    if ($config.clientRoot -and (Test-Path -LiteralPath $config.clientRoot -PathType Container)) {
        $dialog.InitialDirectory = $config.clientRoot
    }
    if ($dialog.ShowDialog($script:form) -eq [Windows.Forms.DialogResult]::OK) {
        Save-ClientExecutable -Executable $dialog.FileName
        return $dialog.FileName
    }
    return ''
}

function Find-ClientExecutable {
    $config = Get-LauncherConfig
    if ($config.clientExecutable -and (Test-Path -LiteralPath $config.clientExecutable -PathType Leaf)) {
        return [string]$config.clientExecutable
    }
    if ($config.clientRoot -and (Test-Path -LiteralPath $config.clientRoot -PathType Container)) {
        foreach ($name in @('metin2client.exe', 'Metin2.exe', 'metin2.exe', 'start.exe', 'launcher.exe')) {
            $candidate = Join-Path $config.clientRoot $name
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                Save-ClientExecutable -Executable $candidate
                return $candidate
            }
        }
    }
    return ''
}

function Start-ConfiguredClient {
    $executable = Find-ClientExecutable
    if (-not $executable) { $executable = Select-ClientExecutable }
    if (-not $executable) {
        [Windows.Forms.MessageBox]::Show(
            'Nie wybrano klienta. Użyj przycisku „Wybierz klienta”.',
            'Metin2 Playerbots', 'OK', 'Information') | Out-Null
        return
    }
    try {
        Start-Process -FilePath $executable -WorkingDirectory (Split-Path -Parent $executable)
        Write-LocalLog "Uruchomiono klienta: $([IO.Path]::GetFileName($executable))"
    }
    catch {
        Write-LocalLog "BŁĄD uruchamiania klienta: $($_.Exception.Message)"
        [Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Nie udało się uruchomić klienta', 'OK', 'Error') | Out-Null
    }
}

function Invoke-QuickProcess {
    param([string]$FileName, [string]$Arguments, [int]$TimeoutMs = 1800)
    try {
        $psi = [Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $FileName
        $psi.Arguments = $Arguments
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $process = [Diagnostics.Process]::Start($psi)
        if (-not $process.WaitForExit($TimeoutMs)) {
            try { $process.Kill() } catch {}
            return [pscustomobject]@{ ExitCode = -1; Output = '' }
        }
        return [pscustomobject]@{
            ExitCode = $process.ExitCode
            Output = $process.StandardOutput.ReadToEnd() + $process.StandardError.ReadToEnd()
        }
    }
    catch { return [pscustomobject]@{ ExitCode = -1; Output = $_.Exception.Message } }
}

function Refresh-Status {
    $dockerInstalled = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
    $dockerProcessesRunning = @(Get-Process -Name 'Docker Desktop', 'com.docker.backend' -ErrorAction SilentlyContinue).Count -gt 0
    $dockerEngineReady = $false
    if ($dockerInstalled) {
        $engineResult = Invoke-QuickProcess -FileName 'docker.exe' -Arguments 'info --format "{{.ServerVersion}}"' -TimeoutMs 2500
        $dockerEngineReady = $engineResult.ExitCode -eq 0
    }
    $script:dockerStatus.Text = if (-not $dockerInstalled) { 'Docker: NIEZAINSTALOWANY' }
        elseif ($dockerEngineReady) { 'Docker: GOTOWY' }
        elseif ($dockerProcessesRunning) { 'Docker: STARTUJE / WYMAGA NAPRAWY' }
        else { 'Docker: ZATRZYMANY' }
    $script:dockerStatus.ForeColor = if ($dockerEngineReady) { [Drawing.Color]::LightGreen }
        elseif ($dockerInstalled) { [Drawing.Color]::Gold }
        else { [Drawing.Color]::Tomato }

    $serverRunning = $false
    if ($dockerEngineReady) {
        $composeDirectory = Join-Path $root 'linux-port\docker'
        $result = Invoke-QuickProcess -FileName 'docker.exe' -Arguments (
            'compose --project-directory "{0}" -f "{1}" ps --services --status running' -f $composeDirectory, $composeFile) -TimeoutMs 1800
        $serverRunning = $result.ExitCode -eq 0 -and $result.Output -match '(?m)^game\s*$'
    }
    $script:serverStatus.Text = if ($serverRunning) { 'Serwer: DZIAŁA' } else { 'Serwer: ZATRZYMANY' }
    $script:serverStatus.ForeColor = if ($serverRunning) { [Drawing.Color]::LightGreen } else { [Drawing.Color]::Silver }

    if ($script:versionLabel) { Update-VersionFooter }
}

# apt/dpkg chatter from a first image build, plus Docker's note about the data
# volume it did not create itself. Both are harmless, but players read the
# word "warning" next to their database and reach for `down -v`, which is the
# one command that would actually destroy the world. Kept in the session log,
# kept out of the on-screen box so the interesting lines stay readable.
$script:M2_NOISY_BUILD = 'already exists but was not created by Docker Compose|Get:\d|Unpacking |Selecting previously|Preparing to unpack|Reading database|Setting up |Suggested packages:|Recommended packages:|The following NEW packages|The following packages will be|debconf:'

# Discord invite the ZIP button falls back to, and the once-per-session cache of
# the support address read from the update manifest.
$script:openContactAfterAction = ''
$script:supportSettingsCache = $null

function Read-SharedText {
    # The child process still holds these files open for writing.
    param([Parameter(Mandatory = $true)][string]$Path)
    try {
        $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8)
            try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
        }
        finally { $stream.Dispose() }
    }
    catch { return $null }
}

function Update-ActionPhase {
    # Turn BuildKit / Compose chatter into a phase name and a step count, so the
    # progress bar and the status line can show real movement during the long
    # first build instead of an endless marquee.
    param([Parameter(Mandatory = $true)][string]$Line)
    $step = [Regex]::Match($Line, '^\s*#\d+\s+\[([^\]]+?)\s+(\d+)/(\d+)\]')
    if ($step.Success) {
        $script:activePhase = $step.Groups[1].Value
        $script:activePhaseStep = [int]$step.Groups[2].Value
        $script:activePhaseTotal = [int]$step.Groups[3].Value
        if (-not $script:activeBuildNoticed) {
            $script:activeBuildNoticed = $true
            Write-LocalLog 'Trwa budowanie obrazów serwera. Przy pierwszym uruchomieniu to normalnie kilkanaście–kilkadziesiąt minut — nie przerywaj.'
        }
        return
    }
    if ($Line -match '^\[faza\]\s*(.+?)\s*(\(|$)') {
        $script:activePhase = $Matches[1]
        $script:activePhaseStep = 0; $script:activePhaseTotal = 0
        return
    }
    if ($Line -match 'transferring context:\s*([\d.]+\s*[kKMG]?B)') {
        $script:activePhase = "przesyłanie plików do budowy ($($Matches[1]))"
        $script:activePhaseStep = 0; $script:activePhaseTotal = 0
        return
    }
    $container = [Regex]::Match($Line, 'Container\s+(\S+)\s+(Creating|Created|Starting|Started|Waiting|Healthy|Recreate|Stopping|Stopped)')
    if ($container.Success) {
        $script:activePhase = "$($container.Groups[1].Value): $($container.Groups[2].Value)"
        $script:activePhaseStep = 0; $script:activePhaseTotal = 0
    }
}

function Update-ActionStatusText {
    if (-not $script:activeProcess -or -not $script:actionStatus) { return }
    $elapsed = (Get-Date) - $script:activeStarted
    $text = 'Trwa: {0}...  {1:mm\:ss}' -f $script:activeAction, $elapsed
    if ($script:activePhaseTotal -gt 0) {
        $pct = [int](100 * $script:activePhaseStep / $script:activePhaseTotal)
        $pct = [Math]::Max(0, [Math]::Min(100, $pct))
        $text += '   —   {0} {1}/{2} ({3}%)' -f $script:activePhase, $script:activePhaseStep, $script:activePhaseTotal, $pct
        if ($script:progress.Style -ne 'Blocks') { $script:progress.Style = 'Blocks' }
        $script:progress.Value = $pct
    }
    elseif ($script:activePhase) {
        $text += '   —   {0}' -f $script:activePhase
    }
    $script:actionStatus.Text = $text
}

function Update-ActionStream {
    # Tail the running action's output into the log while it runs, so a long
    # start does not look like a frozen window.
    if (-not $script:activeProcess) { return }
    foreach ($key in @('out', 'err')) {
        $path = if ($key -eq 'out') { $script:activeOut } else { $script:activeErr }
        if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $content = Read-SharedText -Path $path
        if ($null -eq $content) { continue }
        $offset = if ($key -eq 'out') { $script:activeOutOffset } else { $script:activeErrOffset }
        if ($content.Length -le $offset) { continue }
        $fresh = $content.Substring($offset)
        $lastBreak = $fresh.LastIndexOf("`n")
        if ($lastBreak -lt 0) { continue }
        $complete = $fresh.Substring(0, $lastBreak + 1)
        if ($key -eq 'out') { $script:activeOutOffset = $offset + $complete.Length }
        else { $script:activeErrOffset = $offset + $complete.Length }
        $script:activeOutputAll += $complete
        foreach ($line in ($complete -split '\r?\n')) {
            if (-not $line.Trim()) { continue }
            Update-ActionPhase -Line $line
            if ($line -match $script:M2_NOISY_BUILD) { Write-LocalLog $line -FileOnly }
            else { Write-LocalLog $line }
        }
    }
    Update-ActionStatusText
}

function Complete-LauncherAction {
    if (-not $script:activeProcess) { return }
    try { $script:activeProcess.Refresh() } catch {}
    if (-not $script:activeProcess.HasExited) { return }

    $exitCode = $script:activeProcess.ExitCode
    # Flush whatever the action wrote between the last tick and its exit.
    Update-ActionStream
    foreach ($key in @('out', 'err')) {
        $path = if ($key -eq 'out') { $script:activeOut } else { $script:activeErr }
        if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $content = Read-SharedText -Path $path
        if ($null -eq $content) { continue }
        $offset = if ($key -eq 'out') { $script:activeOutOffset } else { $script:activeErrOffset }
        if ($content.Length -le $offset) { continue }
        $tail = $content.Substring($offset)
        if ($key -eq 'out') { $script:activeOutOffset = $content.Length } else { $script:activeErrOffset = $content.Length }
        $script:activeOutputAll += $tail
        foreach ($line in ($tail -split '\r?\n')) {
            if (-not $line.Trim()) { continue }
            if ($line -match $script:M2_NOISY_BUILD) { Write-LocalLog $line -FileOnly } else { Write-LocalLog $line }
        }
    }
    $output = $script:activeOutputAll

    $action = $script:activeAction
    $launchClient = $script:launchClientAfterAction
    $openSupport = $script:openSupportAfterAction
    $contactUrl = $script:openContactAfterAction
    $script:activeProcess.Dispose()
    $script:activeProcess = $null
    $script:launchClientAfterAction = $false
    $script:openSupportAfterAction = $false
    $script:openContactAfterAction = ''
    $script:progress.Style = 'Blocks'
    $script:progress.Value = 0
    $script:actionStatus.Text = if ($exitCode -eq 0) { "Gotowe: $action" } else { "Błąd: $action (kod $exitCode)" }
    $script:actionStatus.ForeColor = if ($exitCode -eq 0) { [Drawing.Color]::LightGreen } else { [Drawing.Color]::Tomato }
    Write-LocalLog "Zakończono akcję $action, kod $exitCode."
    Refresh-Status

    if ($exitCode -ne 0) {
        $guidance = Get-M2LauncherErrorGuidance -Text $output
        $message = $guidance.Message + [Environment]::NewLine + [Environment]::NewLine + 'Jak naprawić:' + [Environment]::NewLine + $guidance.Remedy
        [Windows.Forms.MessageBox]::Show(
            $message,
            $guidance.Title,
            'OK',
            'Warning') | Out-Null
    }
    if ($exitCode -eq 0 -and $action -like 'Update*' -and (Get-LauncherFingerprint) -ne $script:launcherFingerprint) {
        $answer = [Windows.Forms.MessageBox]::Show(
            "Launcher zostal zaktualizowany.`r`n`r`nTo okno dziala jeszcze na starej wersji - nowe przyciski i poprawki pojawia sie dopiero po ponownym uruchomieniu.`r`n`r`nUruchomic launcher ponownie teraz?",
            'Aktualizacja zainstalowana', 'YesNo', 'Information')
        if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
            Restart-Launcher
            return
        }
        $script:launcherFingerprint = Get-LauncherFingerprint
    }
    if ($exitCode -eq 0 -and $launchClient) { Start-ConfiguredClient }
    if ($script:offerClientAfterAction) {
        $script:offerClientAfterAction = $false
        if ($exitCode -eq 0) { Offer-ClientUpdate }
    }
    if ($exitCode -eq 0 -and $openSupport -and (Test-Path $supportDirectory)) {
        Start-Process explorer.exe -ArgumentList ('"{0}"' -f $supportDirectory)
        if ($contactUrl) { Start-Process $contactUrl }
    }
}

function Confirm-DockerReady {
    # Without this the docker CLI just returns nothing and the caller reports
    # "no databases found", which reads as data loss rather than a stopped engine.
    if (Test-M2DockerRunning) { return $true }
    [Windows.Forms.MessageBox]::Show(
        "Silnik Dockera jest zatrzymany, wiec nie widac zadnych baz.`r`n`r`nKliknij przycisk URUCHOM DOCKER, poczekaj az status u gory zmieni sie na - Docker: GOTOWY - i sprobuj ponownie.`r`n`r`nZadne dane nie zginely: bazy sa na dysku, tylko Docker ich teraz nie pokazuje.",
        'Docker jest zatrzymany', 'OK', 'Warning') | Out-Null
    return $false
}

function Get-SupportSettings {
    if ($null -eq $script:supportSettingsCache) {
        try { $script:supportSettingsCache = Get-M2SupportSettings -Config (Get-LauncherConfig) }
        catch {
            Write-LocalLog "Nie udalo sie odczytac adresu zgloszen: $($_.Exception.Message)" -FileOnly
            $script:supportSettingsCache = [pscustomobject]@{ UploadUrl = ''; ContactUrl = 'https://discord.gg/pt5tvnrN6'; Source = 'none' }
        }
    }
    return $script:supportSettingsCache
}

function Get-BotCountFromEnv {
    $envPath = Join-Path $root 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = [Regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^PLAYERBOT_AUTOSPAWN_COUNT=(\d+)\s*$')
        if ($match.Success) { return [int]$match.Groups[1].Value }
    }
    return 350
}

function Get-LauncherFingerprint {
    # An update replaces the launcher's own files, but this process already read
    # them - the new buttons cannot appear until it restarts.
    $stamps = New-Object System.Collections.Generic.List[string]
    foreach ($file in @($PSCommandPath, $cliLauncher, $modulePath, $diagnosticsModulePath)) {
        if (Test-Path -LiteralPath $file -PathType Leaf) {
            $stamps.Add(((Get-Item -LiteralPath $file).LastWriteTimeUtc.Ticks).ToString())
        }
    }
    return ($stamps -join '|')
}

function Restart-Launcher {
    $batch = Join-Path $root 'Metin2-Launcher-GUI.bat'
    try {
        if (Test-Path -LiteralPath $batch -PathType Leaf) {
            Start-Process -FilePath $batch -WorkingDirectory $root
        }
        else {
            # -STA matters: WinForms will not start without it.
            Start-Process -FilePath 'powershell.exe' -WorkingDirectory $root -ArgumentList @(
                '-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath)
        }
        Write-LocalLog 'Uruchamiam launcher ponownie po aktualizacji.'
        $script:form.Close()
    }
    catch {
        [Windows.Forms.MessageBox]::Show(
            ("Nie udalo sie uruchomic launchera ponownie: {0}`r`n`r`nZamknij to okno i uruchom launcher recznie." -f $_.Exception.Message),
            'Restart launchera', 'OK', 'Warning') | Out-Null
    }
}

function Get-InstalledServerVersion {
    # Same reasoning as Read-State in the text launcher: while a rebuild is
    # outstanding the files on disk are ahead of the containers, so the version
    # they claim must not be used to decide that nothing needs doing.
    if (Test-Path -LiteralPath (Join-Path $root '.m2launcher-rebuild-pending') -PathType Leaf) {
        return 'unknown'
    }
    $statePath = Join-Path $root '.m2launcher-state.json'
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$state.server) { return ([string]$state.server).Trim() }
        }
        catch { }
    }
    $versionFile = Join-Path $root 'VERSION'
    if (Test-Path -LiteralPath $versionFile -PathType Leaf) {
        return (Get-Content -LiteralPath $versionFile -Raw).Trim()
    }
    return 'unknown'
}

function Get-InstalledClientVersion {
    # What a client update recorded, else what the full package shipped
    # (CLIENT_VERSION beside VERSION, put there by New-M2DeployTree.ps1).
    $statePath = Join-Path $root '.m2launcher-state.json'
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$state.client -and [string]$state.client -ne 'unknown') { return ([string]$state.client).Trim() }
        }
        catch { }
    }
    $marker = Join-Path $root 'CLIENT_VERSION'
    if (Test-Path -LiteralPath $marker -PathType Leaf) {
        return (Get-Content -LiteralPath $marker -Raw).Trim()
    }
    return 'unknown'
}

# The versions the player said NO to at startup, so the same question is not
# asked at every start - a newer version asks again. Its own file: Save-State
# in the text launcher rewrites .m2launcher-state.json with three fields only.
$script:offersPath = Join-Path $root '.m2launcher-offers.json'
function Read-DeclinedOffers {
    $declined = @{ server = ''; client = '' }
    if (Test-Path -LiteralPath $script:offersPath -PathType Leaf) {
        try {
            $saved = Get-Content -LiteralPath $script:offersPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ([string]$saved.server) { $declined.server = [string]$saved.server }
            if ([string]$saved.client) { $declined.client = [string]$saved.client }
        }
        catch { }
    }
    return $declined
}
function Save-DeclinedOffer {
    param([string]$Component, [string]$Version)
    $declined = Read-DeclinedOffers
    $declined[$Component] = $Version
    try {
        [pscustomobject]$declined | ConvertTo-Json | Set-Content -LiteralPath $script:offersPath -Encoding UTF8
    }
    catch { }
}

function Test-VersionNewer {
    param([string]$Installed, [string]$Available)
    if (-not $Available) { return $false }
    if (-not $Installed -or $Installed -eq 'unknown') { return $true }
    return -not $Installed.Trim().Equals($Available.Trim(), [StringComparison]::OrdinalIgnoreCase)
}

$script:latestManifest = $null
$script:offerClientAfterAction = $false
$script:startupOfferDone = $false

function Offer-ClientUpdate {
    # Only on the 2.x line: there the manifest's client component is the
    # ordinary client package. On r40250 it is the experimental GM panel,
    # which nobody should be nagged into at startup.
    if (-not $script:clientUpdateIsPlain -or -not $script:latestManifest) { return }
    $clientProperty = $script:latestManifest.PSObject.Properties['client']
    if (-not $clientProperty -or -not $clientProperty.Value -or -not [string]$clientProperty.Value.version) { return }
    $available = ([string]$clientProperty.Value.version).Trim()
    $installed = Get-InstalledClientVersion
    if (-not (Test-VersionNewer -Installed $installed -Available $available)) { return }
    if ((Read-DeclinedOffers).client -eq $available) { return }
    $config = Get-LauncherConfig
    if (-not [string]$config.clientRoot) {
        Write-LocalLog "Dostepna wersja klienta $available, ale folder klienta nie jest ustawiony - pomijam pytanie."
        return
    }
    $answer = [Windows.Forms.MessageBox]::Show(
        ((T 'startupClientUpdate') -f $available, $installed),
        (T 'startupUpdateTitle'), 'YesNo', 'Question')
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) {
        Save-DeclinedOffer -Component 'client' -Version $available
        Write-LocalLog "Aktualizacja klienta $available odlozona."
        return
    }
    Start-LauncherAction -Action 'UpdateClient' -Yes
}

function Offer-StartupUpdates {
    # Once per session, on the first manifest read: the server first, and the
    # client after the server action has finished (two actions cannot run at
    # once), or right away when the server is current.
    if ($script:startupOfferDone -or -not $script:latestManifest) { return }
    $script:startupOfferDone = $true
    if ($script:activeProcess -and -not $script:activeProcess.HasExited) { return }
    $installed = Get-InstalledServerVersion
    $available = $script:latestServerVersion
    if ($available -and (Test-VersionNewer -Installed $installed -Available $available) -and
            (Read-DeclinedOffers).server -ne $available) {
        $answer = [Windows.Forms.MessageBox]::Show(
            ((T 'startupServerUpdate') -f $available, $installed),
            (T 'startupUpdateTitle'), 'YesNo', 'Question')
        if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
            $script:offerClientAfterAction = $true
            Start-LauncherAction -Action 'UpdateServer' -Yes
            return
        }
        Save-DeclinedOffer -Component 'server' -Version $available
        Write-LocalLog "Aktualizacja serwera $available odlozona."
    }
    Offer-ClientUpdate
}

function Show-BotCountDialog {
    # Slider instead of a typed number: the range is a property of the world, and
    # dragging is far friendlier than guessing a value. The maximum matches the
    # canonical cohort the seed creates - 1500 for Chunjo alone (PID 4..1503) and
    # 2500 once the other two kingdoms are switched on (M2_PLAYERBOT_KINGDOMS=1,
    # PID 4..2503). It stopped at 1500 while the world already held 2500, so a
    # thousand seeded bots could not be asked for from here at all. Asking for
    # more than a world holds is safe and always was: the core spawns what its
    # registry has and logs requested/registered/started.
    param([int]$Current = 350)
    $dialog = [Windows.Forms.Form]::new()
    $dialog.Text = (T 'botDialog')
    $dialog.Size = [Drawing.Size]::new(480, 260)
    $dialog.StartPosition = 'CenterParent'
    $dialog.FormBorderStyle = 'FixedDialog'
    $dialog.MaximizeBox = $false
    $dialog.MinimizeBox = $false

    $info = [Windows.Forms.Label]::new()
    $info.Text = "Ilu botów ma grać jednocześnie?`r`nEfektywny limit to liczba botów w Twoim świecie: 1500 dla samego Chunjo,`r`n2500 przy włączonych trzech królestwach. Zmiana wymaga restartu serwera."
    $info.Location = [Drawing.Point]::new(14, 12)
    $info.Size = [Drawing.Size]::new(440, 54)
    $dialog.Controls.Add($info)

    $valueLabel = [Windows.Forms.Label]::new()
    $valueLabel.Name = 'valueLabel'
    $valueLabel.Font = [Drawing.Font]::new('Segoe UI Semibold', 15)
    $valueLabel.Location = [Drawing.Point]::new(14, 70)
    $valueLabel.Size = [Drawing.Size]::new(440, 32)
    $dialog.Controls.Add($valueLabel)

    $bar = [Windows.Forms.TrackBar]::new()
    $bar.Name = 'botBar'
    $bar.Minimum = 0
    $bar.Maximum = 2500
    $bar.TickFrequency = 50
    $bar.SmallChange = 1
    $bar.LargeChange = 25
    $bar.Location = [Drawing.Point]::new(12, 104)
    $bar.Size = [Drawing.Size]::new(442, 45)
    $bar.Value = [Math]::Max(0, [Math]::Min(2500, $Current))
    $dialog.Controls.Add($bar)
    $valueLabel.Text = "Boty: $($bar.Value)"
    # $this/FindForm keeps the handler independent of captured locals.
    $bar.Add_ValueChanged({
            $form = $this.FindForm()
            if ($form) {
                $label = $form.Controls['valueLabel']
                if ($label) { $label.Text = "Boty: $($this.Value)" }
            }
        })

    $okButton = [Windows.Forms.Button]::new()
    $okButton.Text = (T 'apply')
    $okButton.Location = [Drawing.Point]::new(252, 168)
    $okButton.Size = [Drawing.Size]::new(100, 32)
    $okButton.DialogResult = [Windows.Forms.DialogResult]::OK
    $dialog.Controls.Add($okButton)

    $cancelButton = [Windows.Forms.Button]::new()
    $cancelButton.Text = (T 'cancel')
    $cancelButton.Location = [Drawing.Point]::new(358, 168)
    $cancelButton.Size = [Drawing.Size]::new(96, 32)
    $cancelButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $dialog.Controls.Add($cancelButton)
    $dialog.AcceptButton = $okButton
    $dialog.CancelButton = $cancelButton

    $result = $dialog.ShowDialog()
    $chosen = $bar.Value
    $dialog.Dispose()
    if ($result -ne [Windows.Forms.DialogResult]::OK) { return $null }
    return [int]$chosen
}

function Get-GuiTargetVolume {
    $statePath = Join-Path $root '.m2install.json'
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            $vp = $state.PSObject.Properties['databaseVolume']
            if ($vp -and [string]$vp.Value) { return [string]$vp.Value }
            if ([string]$state.projectName) { return "$([string]$state.projectName)_db-data" }
        }
        catch { }
    }
    $envPath = Join-Path $root 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = [Regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^M2_COMPOSE_PROJECT_NAME=([a-z0-9][a-z0-9_-]+)\s*$')
        if ($match.Success) { return "$($match.Groups[1].Value)_db-data" }
    }
    return ''
}

function Start-LauncherAction {
    param(
        [Parameter(Mandatory = $true)][string]$Action,
        [switch]$Yes,
        [switch]$LaunchClient,
        [switch]$OpenSupport,
        [string[]]$ExtraArgs = @()
    )
    if ($script:activeProcess -and -not $script:activeProcess.HasExited) {
        [Windows.Forms.MessageBox]::Show('Poczekaj na zakończenie bieżącej operacji.', 'Launcher pracuje', 'OK', 'Information') | Out-Null
        return
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $script:activeOut = Join-Path $logDirectory ("action-$stamp.out.log")
    $script:activeErr = Join-Path $logDirectory ("action-$stamp.err.log")
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $cliLauncher), '-Action', $Action)
    if ($Yes) { $arguments += '-Yes' }
    if ($ExtraArgs -and $ExtraArgs.Count -gt 0) { $arguments += $ExtraArgs }
    Write-LocalLog "Rozpoczęto akcję $Action."
    $script:activeAction = $Action
    $script:launchClientAfterAction = [bool]$LaunchClient
    $script:openSupportAfterAction = [bool]$OpenSupport
    # Live-progress state for this run.
    $script:activeOutOffset = 0
    $script:activeErrOffset = 0
    $script:activeOutputAll = ''
    $script:activeStarted = Get-Date
    $script:activePhase = ''
    $script:activePhaseStep = 0
    $script:activePhaseTotal = 0
    $script:activeBuildNoticed = $false
    $script:actionStatus.Text = "Trwa: $Action..."
    $script:actionStatus.ForeColor = [Drawing.Color]::Gold
    $script:progress.Style = 'Marquee'
    $script:activeProcess = Start-Process -FilePath 'powershell.exe' `
        -ArgumentList $arguments -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $script:activeOut -RedirectStandardError $script:activeErr
    # Start-Process -PassThru with redirected stdout/stderr does not keep the OS
    # process handle, so a later $activeProcess.ExitCode reads $null even after
    # the process has exited cleanly. That made every action -- including a fully
    # successful start -- report "Błąd: ... (kod )" with an empty code. Touching
    # .Handle now caches it so ExitCode is readable in Complete-LauncherAction.
    try { $null = $script:activeProcess.Handle } catch {}
}

function Install-Or-Prepare {
    # @(...) round the whole pipeline, not only its input: Where-Object hands
    # back a bare string when one file is missing, and under Set-StrictMode a
    # string has no .Count - the button threw "The property 'Count' cannot be
    # found" at exactly the player whose package was incomplete.
    $missing = @(@($cliLauncher, $composeFile, $modulePath) | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
    if ($missing.Count -gt 0) {
        [Windows.Forms.MessageBox]::Show('Paczka jest niekompletna. Rozpakuj ponownie całe archiwum RAR.', 'Brak plików', 'OK', 'Error') | Out-Null
        return
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        $answer = [Windows.Forms.MessageBox]::Show(
            'Docker Desktop nie jest zainstalowany. Czy otworzyć oficjalną stronę pobierania?',
            'Wymagany Docker Desktop', 'YesNo', 'Question')
        if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
            Start-Process 'https://www.docker.com/products/docker-desktop/'
        }
        return
    }

    $preflight = Get-M2DockerPreflight -ServerRoot $root
    Write-LocalLog (Format-M2DockerPreflightReport -Report $preflight)
    if (-not $preflight.CanStart) {
        [Windows.Forms.MessageBox]::Show(
            ((@($preflight.BlockingIssues) -join [Environment]::NewLine) + [Environment]::NewLine + [Environment]::NewLine + 'Po naprawie uruchom launcher ponownie.'),
            'Komputer nie jest jeszcze gotowy',
            'OK',
            'Warning') | Out-Null
        return
    }

    # This button prepares a package whose game sources are already on disk;
    # it never fetches them, because they are the operator's own r40250 files
    # and only installer\install.ps1 knows how to take them from that package.
    # Until now it said "Paczka jest gotowa" regardless - and a player whose
    # sources were missing pressed it, was told the package was ready, pressed
    # GRAJ and got fifteen Docker errors. Reported from the Discord: "re-running
    # the installer through Install in GUI did not restore the sources" - it
    # could not have, this is not the installer. Say which it is.
    $gameContext = Join-Path $root 'linux-port\docker\game\src'
    $requiredContext = @(Get-M2RequiredGameContext -ServerRoot $root)
    $missingContext = @($requiredContext | Where-Object { -not (Test-Path -LiteralPath (Join-Path $gameContext $_)) })
    # The database dumps are the other half of what the installer takes out
    # of the package, and the half nobody saw missing until MariaDB came up
    # empty: name them here with the sources.
    $missingContext += @(Get-M2MissingSqlDumps -ServerRoot $root | ForEach-Object { 'mariadb\initdb.d\dumps\' + $_ })
    if ($missingContext.Count -gt 0) {
        $installerPath = Join-Path $root 'installer\install.ps1'
        Write-LocalLog ("Brak zrodel gry w " + $gameContext + ": " + ($missingContext -join ', '))
        [Windows.Forms.MessageBox]::Show(
            ("Ten przycisk przygotowuje paczke, ktora ma juz na dysku zrodla gry - a tu ich nie ma." + [Environment]::NewLine +
             "Brakuje: " + ($missingContext -join ', ') + [Environment]::NewLine + [Environment]::NewLine +
             "Zrodla pochodza z Twojej wlasnej paczki serwera r40250 i zaden przycisk launchera ani zadna aktualizacja ich nie pobiera - " +
             "robi to wylacznie instalator, ktory wyciaga z tej paczki to, czego trzeba." + [Environment]::NewLine + [Environment]::NewLine +
             "Uruchom w PowerShell jako administrator:" + [Environment]::NewLine +
             "  `$env:M2_SRC_ARCHIVE = 'C:\sciezka\do\paczki-r40250.zip'" + [Environment]::NewLine +
             "  & '" + $installerPath + "'" + [Environment]::NewLine + [Environment]::NewLine +
             "Baza, postacie i ustawienia zostaja nietkniete."),
            'Brak zrodel gry - potrzebny instalator', 'OK', 'Warning') | Out-Null
        return
    }

    if (-not (Find-ClientExecutable)) { [void](Select-ClientExecutable) }
    try {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $shortcutPath = Join-Path $desktop 'Metin2 Playerbots.lnk'
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = Join-Path $root 'Metin2-Launcher-GUI.bat'
        $shortcut.WorkingDirectory = $root
        $shortcut.Description = 'Metin2 Singleplayer Playerbots'
        $shortcut.Save()
        Write-LocalLog 'Sprawdzono paczkę i utworzono skrót na pulpicie.'
    }
    catch { Write-LocalLog "Nie udało się utworzyć skrótu: $($_.Exception.Message)" }
    [Windows.Forms.MessageBox]::Show(
        'Paczka jest gotowa. Utworzono skrót na pulpicie. Kliknij GRAJ, aby uruchomić Docker, serwer i klienta.',
        'Gotowe', 'OK', 'Information') | Out-Null
}

$script:launcherFingerprint = Get-LauncherFingerprint

$script:form = [Windows.Forms.Form]::new()
$script:form.Text = (T 'formTitle')
$script:form.Size = [Drawing.Size]::new(780, 806)
$script:form.MinimumSize = [Drawing.Size]::new(780, 764)
$script:form.StartPosition = 'CenterScreen'
$script:form.BackColor = [Drawing.Color]::FromArgb(24, 25, 29)
$script:form.ForeColor = [Drawing.Color]::White
$script:form.Font = [Drawing.Font]::new('Segoe UI', 9)

$title = [Windows.Forms.Label]::new()
$title.Text = (T 'title')
$title.Font = [Drawing.Font]::new('Segoe UI Semibold', 19)
$title.ForeColor = [Drawing.Color]::FromArgb(247, 194, 66)
$title.Location = [Drawing.Point]::new(24, 18)
$title.Size = [Drawing.Size]::new(710, 38)
$script:form.Controls.Add($title)

$subtitle = [Windows.Forms.Label]::new()
$subtitle.Text = (T 'subtitle')
$subtitle.Location = [Drawing.Point]::new(27, 58)
$subtitle.Size = [Drawing.Size]::new(700, 24)
$subtitle.ForeColor = [Drawing.Color]::Silver
$script:form.Controls.Add($subtitle)

$script:dockerStatus = [Windows.Forms.Label]::new()
$script:dockerStatus.Location = [Drawing.Point]::new(28, 92)
$script:dockerStatus.Size = [Drawing.Size]::new(310, 25)
$script:dockerStatus.Font = [Drawing.Font]::new('Segoe UI Semibold', 10)
$script:form.Controls.Add($script:dockerStatus)

$script:serverStatus = [Windows.Forms.Label]::new()
$script:serverStatus.Location = [Drawing.Point]::new(375, 92)
$script:serverStatus.Size = [Drawing.Size]::new(300, 25)
$script:serverStatus.Font = [Drawing.Font]::new('Segoe UI Semibold', 10)
$script:form.Controls.Add($script:serverStatus)

$installButton = New-Button (T 'install') 28 128 338 58 ([Drawing.Color]::FromArgb(88, 82, 160))
$playButton = New-Button (T 'play') 388 128 338 58 ([Drawing.Color]::FromArgb(27, 150, 88))
$dockerButton = New-Button (T 'docker') 28 202 218 50
$stopButton = New-Button (T 'stop') 268 202 218 50 ([Drawing.Color]::FromArgb(180, 75, 55))
$panelButton = New-Button (T 'panel') 508 202 218 50 ([Drawing.Color]::FromArgb(180, 125, 35))
$clientButton = New-Button (T 'client') 28 266 218 48 ([Drawing.Color]::FromArgb(75, 90, 120))
$updateButton = New-Button (T 'update') 268 266 218 48 ([Drawing.Color]::FromArgb(75, 90, 120))
$bundleButton = New-Button (T 'bundle') 508 266 218 48 ([Drawing.Color]::FromArgb(75, 90, 120))
$diagnosticsButton = New-Button (T 'diagnostics') 28 328 218 45 ([Drawing.Color]::FromArgb(45, 110, 190))
$openLogButton = New-Button (T 'openLog') 262 328 218 45 ([Drawing.Color]::FromArgb(58, 62, 72))
$folderButton = New-Button (T 'logFolder') 496 328 230 45 ([Drawing.Color]::FromArgb(58, 62, 72))
$botCountButton = New-Button (T 'botCount') 28 380 218 32 ([Drawing.Color]::FromArgb(120, 95, 40))
$importDbButton = New-Button (T 'importDb') 262 380 218 32 ([Drawing.Color]::FromArgb(70, 120, 90))
$repairDbButton = New-Button (T 'repairDb') 496 380 230 32 ([Drawing.Color]::FromArgb(150, 90, 55))
$dbAccessButton = New-Button (T 'dbAccess') 28 418 218 32 ([Drawing.Color]::FromArgb(70, 100, 130))
# The optional, experimental client half of the GM panel (F9): the server half
# rides in every update, this button fetches the client package from the
# manifest's `client` component and swaps pack/root.eix + root.epk.
$gmPanelButton = New-Button (T 'gmPanel') 262 418 218 32 ([Drawing.Color]::FromArgb(120, 70, 130))
# On the mt2009 line the client update is the ordinary one - the packs the
# server's root points at - and not the experimental GM panel.
$script:clientUpdateIsPlain = ((Get-M2ServerEngine -ServerRoot $root) -ne 'r40250')
if ($script:clientUpdateIsPlain) { $gmPanelButton.Text = (T 'updateClient') }
# Backup, restore and "start over" behind one button: reported from the
# Discord as "the launcher can import a database but nothing says how to
# export one", together with a wish to get back to a fresh install.
$worldBackupButton = New-Button (T 'worldBackup') 496 418 230 32 ([Drawing.Color]::FromArgb(70, 120, 90))

# The language switch sits with the other small buttons rather than in a menu:
# somebody who cannot read the window needs to find it without reading anything.
$languageButton = New-Button (T 'language') 508 702 218 28 ([Drawing.Color]::FromArgb(60, 70, 95))
$languageButton.Add_Click({ Switch-LauncherLanguage })

foreach ($button in @($installButton, $playButton, $dockerButton, $stopButton, $panelButton, $clientButton, $updateButton, $bundleButton, $diagnosticsButton, $openLogButton, $folderButton, $botCountButton, $importDbButton, $repairDbButton, $dbAccessButton, $gmPanelButton, $worldBackupButton, $languageButton)) {
    $script:form.Controls.Add($button)
}

$script:actionStatus = [Windows.Forms.Label]::new()
$script:actionStatus.Text = (T 'ready')
$script:actionStatus.Location = [Drawing.Point]::new(28, 462)
$script:actionStatus.Size = [Drawing.Size]::new(690, 24)
$script:actionStatus.Font = [Drawing.Font]::new('Segoe UI Semibold', 9)
$script:form.Controls.Add($script:actionStatus)

$script:progress = [Windows.Forms.ProgressBar]::new()
$script:progress.Location = [Drawing.Point]::new(28, 490)
$script:progress.Size = [Drawing.Size]::new(698, 12)
$script:form.Controls.Add($script:progress)

$script:logBox = [Windows.Forms.TextBox]::new()
$script:logBox.Location = [Drawing.Point]::new(28, 518)
$script:logBox.Size = [Drawing.Size]::new(698, 122)
$script:logBox.Multiline = $true
$script:logBox.ReadOnly = $true
$script:logBox.ScrollBars = 'Vertical'
$script:logBox.BackColor = [Drawing.Color]::FromArgb(12, 13, 16)
$script:logBox.ForeColor = [Drawing.Color]::Gainsboro
$script:logBox.Font = [Drawing.Font]::new('Consolas', 8.5)
$script:form.Controls.Add($script:logBox)

$footer = [Windows.Forms.Label]::new()
$footer.Text = (T 'footer')
$footer.Location = [Drawing.Point]::new(28, 650)
$footer.Size = [Drawing.Size]::new(700, 25)
$footer.ForeColor = [Drawing.Color]::DarkGray
$script:form.Controls.Add($footer)


$script:versionLabel = [Windows.Forms.Label]::new()
$script:versionLabel.Location = [Drawing.Point]::new(28, 674)
$script:versionLabel.Size = [Drawing.Size]::new(470, 54)
$script:versionLabel.ForeColor = [Drawing.Color]::Silver
$script:versionLabel.Font = [Drawing.Font]::new('Segoe UI Semibold', 9)
$script:form.Controls.Add($script:versionLabel)

$script:latestServerVersion = $null
$script:latestClientVersion = $null
$script:latestVersionChecked = $false

function Get-LauncherVersionOnDisk {
    # The launcher ships inside the server package, so the VERSION file beside
    # it is its version. Read at startup for what this window runs, and again
    # for the footer: after an update applied in this session the file is
    # ahead of the process, and the footer says so.
    $path = Join-Path $root 'VERSION'
    try {
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $text = (Get-Content -LiteralPath $path -Raw -ErrorAction Stop).Trim()
            if ($text) { return $text }
        }
    }
    catch { }
    return 'nieznana'
}
$script:launcherVersion = Get-LauncherVersionOnDisk

function Set-LatestVersionsFromManifest {
    param($Manifest)
    if (-not $Manifest) { return }
    $serverProperty = $Manifest.PSObject.Properties['server']
    if ($serverProperty -and $serverProperty.Value -and [string]$serverProperty.Value.version) {
        $script:latestServerVersion = ([string]$serverProperty.Value.version).Trim()
    }
    $clientProperty = $Manifest.PSObject.Properties['client']
    if ($clientProperty -and $clientProperty.Value -and [string]$clientProperty.Value.version) {
        $script:latestClientVersion = ([string]$clientProperty.Value.version).Trim()
    }
}

function Update-VersionFooter {
    # The manifest lives behind GitHub's anonymous per-IP budget, so it is read
    # once per session and whenever the player asks for a check - never on the
    # 8-second status timer, which would spend that budget for nothing.
    $installed = Get-InstalledServerVersion
    $installedText = if ($installed -and $installed -ne 'unknown') { $installed } else { 'nieznana (przebudowa w toku)' }
    $latestText = if ($script:latestServerVersion) { $script:latestServerVersion }
        elseif ($script:latestVersionChecked) { 'nie udalo sie sprawdzic' }
        else { 'sprawdzanie...' }
    $latestClientText = if ($script:latestClientVersion) { $script:latestClientVersion }
        elseif ($script:latestVersionChecked) { 'nie udalo sie sprawdzic' }
        else { 'sprawdzanie...' }
    # Three lines, asked for on the Discord: the server, the launcher itself
    # (its newest version is the server package's) and the client.
    $onDisk = Get-LauncherVersionOnDisk
    $launcherText = $script:launcherVersion
    if ($onDisk -ne $script:launcherVersion) {
        $launcherText = '{0} (na dysku {1} - uruchom launcher ponownie)' -f $script:launcherVersion, $onDisk
    }
    $clientInstalled = Get-InstalledClientVersion
    $clientText = if ($clientInstalled -and $clientInstalled -ne 'unknown') { $clientInstalled } else { 'nieznana' }
    $script:versionLabel.Text = ("Serwer: {0}   |   najnowszy: {1}`r`nLauncher: {2}   |   najnowszy: {3}`r`nKlient: {4}   |   najnowszy: {5}" -f
        $installedText, $latestText, $launcherText, $latestText, $clientText, $latestClientText)
    $upToDate = $script:latestServerVersion -and $installed -and $installed -ne 'unknown' -and
        $installed.Equals($script:latestServerVersion, [StringComparison]::OrdinalIgnoreCase)
    $script:versionLabel.ForeColor = if ($upToDate) { [Drawing.Color]::LightGreen }
        elseif ($script:latestServerVersion) { [Drawing.Color]::Gold }
        else { [Drawing.Color]::Silver }
}

function Read-LatestServerVersion {
    param([switch]$Force)
    if ($script:latestVersionChecked -and -not $Force) { return }
    $script:latestVersionChecked = $true
    try {
        $config = Get-M2LauncherConfig -ServerRoot $root -ConfigPath $configPath
        $manifest = Get-M2UpdateManifest -Source ([string]$config.manifestUrl) -TimeoutSec 8
        $script:latestManifest = $manifest
        Set-LatestVersionsFromManifest -Manifest $manifest
    }
    catch { }
    Update-VersionFooter
    Offer-StartupUpdates
}

$installButton.Add_Click({ Install-Or-Prepare })
$playButton.Add_Click({
    if (-not (Find-ClientExecutable)) {
        if (-not (Select-ClientExecutable)) { return }
    }
    Start-LauncherAction -Action 'Start' -LaunchClient
})
$dockerButton.Add_Click({ Start-LauncherAction -Action 'StartDocker' })
$stopButton.Add_Click({
    $answer = [Windows.Forms.MessageBox]::Show(
        'Zatrzymać serwer i Docker Desktop? Postacie, baza i postęp botów zostaną zachowane.',
        'Bezpieczne zatrzymanie', 'YesNo', 'Question')
    if ($answer -eq [Windows.Forms.DialogResult]::Yes) { Start-LauncherAction -Action 'StopAll' }
})
function Get-M2PanelAddresses {
    # Both web panels of the same world, at whatever ports this installation
    # actually publishes them on. The defaults match the compose file; a world
    # whose .env moves a port is followed rather than guessed at.
    param([Parameter(Mandatory = $true)][string]$ServerRoot)

    $classic = 7788
    $seban = 7790
    $envPath = Join-Path $ServerRoot 'linux-port\docker\.env'
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = Select-String -LiteralPath $envPath -Pattern '^M2_PANEL_PUBLIC_PORT=(\d+)$' | Select-Object -First 1
        if ($match) { $classic = [int]$match.Matches[0].Groups[1].Value }
        $match = Select-String -LiteralPath $envPath -Pattern '^M2_SEBAN_PANEL_PORT=(\d+)$' | Select-Object -First 1
        if ($match) { $seban = [int]$match.Matches[0].Groups[1].Value }
    }
    return [pscustomobject]@{
        ClassicUrl = "http://127.0.0.1:$classic/map"
        SebanUrl   = "http://127.0.0.1:$seban/"
        ClassicPort = $classic
        SebanPort   = $seban
    }
}

function Show-PanelPasswordDialog {
    # In-process and read-only: an action would print the passphrase through the
    # launcher log, and the launcher log travels in support bundles that get
    # posted on the Discord. Same rule as the database credentials dialog.
    $envPath = Join-Path $root 'linux-port\docker\.env'
    $passphrase = ''
    if (Test-Path -LiteralPath $envPath -PathType Leaf) {
        $match = [Regex]::Match([IO.File]::ReadAllText($envPath), '(?m)^M2_PANEL_PASSWORD=(.+?)\s*$')
        if ($match.Success) { $passphrase = $match.Groups[1].Value }
    }
    if (-not $passphrase) {
        [Windows.Forms.MessageBox]::Show(
            "W pliku .env nie ma jeszcze hasla do panelu.`r`n`r`nKliknij GRAJ raz - launcher je uzupelni i pokaze.",
            'Haslo do panelu', 'OK', 'Information') | Out-Null
        return
    }

    $dialog = [Windows.Forms.Form]::new()
    $dialog.Text = 'Haslo do panelu WWW'
    $dialog.Size = [Drawing.Size]::new(520, 250)
    $dialog.StartPosition = 'CenterParent'
    $dialog.FormBorderStyle = 'FixedDialog'
    $dialog.MaximizeBox = $false
    $dialog.MinimizeBox = $false

    $info = [Windows.Forms.Label]::new()
    $info.Text = 'Panel ma jedno haslo i nie ma loginu. Zaznacz je i skopiuj.'
    $info.Location = [Drawing.Point]::new(16, 14)
    $info.Size = [Drawing.Size]::new(480, 20)
    $dialog.Controls.Add($info)

    $box = [Windows.Forms.TextBox]::new()
    $box.Text = $passphrase
    $box.ReadOnly = $true
    $box.Location = [Drawing.Point]::new(16, 40)
    $box.Size = [Drawing.Size]::new(480, 26)
    $box.Font = [Drawing.Font]::new('Consolas', 12)
    $dialog.Controls.Add($box)

    $hint = [Windows.Forms.Label]::new()
    $hint.Text = ('Jesli panel go nie przyjmuje, zapamietal starsze haslo z pierwszego' + [Environment]::NewLine +
        'uruchomienia. Reset kasuje jeden plik konfiguracyjny panelu i ustawia' + [Environment]::NewLine +
        'haslo powyzej. Swiat, postacie i boty sa w bazie i nie sa tym ruszane.')
    $hint.Location = [Drawing.Point]::new(16, 76)
    $hint.Size = [Drawing.Size]::new(480, 60)
    $dialog.Controls.Add($hint)

    $resetButton = [Windows.Forms.Button]::new()
    $resetButton.Text = 'Zresetuj haslo panelu'
    $resetButton.Location = [Drawing.Point]::new(16, 148)
    $resetButton.Size = [Drawing.Size]::new(230, 34)
    $resetButton.DialogResult = [Windows.Forms.DialogResult]::Yes
    $dialog.Controls.Add($resetButton)

    $closeButton = [Windows.Forms.Button]::new()
    $closeButton.Text = 'Zamknij'
    $closeButton.Location = [Drawing.Point]::new(396, 148)
    $closeButton.Size = [Drawing.Size]::new(100, 34)
    $closeButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $dialog.Controls.Add($closeButton)
    $dialog.CancelButton = $closeButton

    $answer = $dialog.ShowDialog()
    $dialog.Dispose()
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
    Start-LauncherAction -Action 'PanelPassword' -Yes
}

function Show-PanelChoiceDialog {
    # Two panels look at the same world and neither replaces the other, so the
    # button asks instead of deciding: the classic one is the map and the
    # controls this launcher has always opened, seban latino's is the wider
    # view - profiles, rankings, the economy's history, the host's load.
    param([Parameter(Mandatory = $true)]$Addresses)

    $dialog = [Windows.Forms.Form]::new()
    $dialog.Text = (T 'panelDialog')
    $dialog.Size = [Drawing.Size]::new(520, 250)
    $dialog.StartPosition = 'CenterParent'
    $dialog.FormBorderStyle = 'FixedDialog'
    $dialog.MaximizeBox = $false
    $dialog.MinimizeBox = $false

    $info = [Windows.Forms.Label]::new()
    $info.Text = (T 'panelInfo')
    $info.Location = [Drawing.Point]::new(16, 14)
    $info.Size = [Drawing.Size]::new(480, 22)
    $dialog.Controls.Add($info)

    $classicButton = [Windows.Forms.Button]::new()
    $classicButton.Text = ("{0}  -  port {1}" -f (T 'panelClassic'), $Addresses.ClassicPort)
    $classicButton.Location = [Drawing.Point]::new(16, 46)
    $classicButton.Size = [Drawing.Size]::new(480, 56)
    $classicButton.DialogResult = [Windows.Forms.DialogResult]::Yes
    $dialog.Controls.Add($classicButton)

    $sebanButton = [Windows.Forms.Button]::new()
    $sebanButton.Text = ("{0}  -  port {1}" -f (T 'panelSeban'), $Addresses.SebanPort)
    $sebanButton.Location = [Drawing.Point]::new(16, 110)
    $sebanButton.Size = [Drawing.Size]::new(480, 56)
    $sebanButton.DialogResult = [Windows.Forms.DialogResult]::No
    $dialog.Controls.Add($sebanButton)

    # The third thing somebody pressing this button may actually want.
    # "podajcie te kody do gm bo ja nie moge na www wejsc", "ja nie mam zadnego
    # hasla nawet w panelu tieru" - it is one line in .env and nothing showed it.
    $passwordButton = [Windows.Forms.Button]::new()
    $passwordButton.Text = (T 'panelPw')
    $passwordButton.Location = [Drawing.Point]::new(16, 174)
    $passwordButton.Size = [Drawing.Size]::new(370, 30)
    $passwordButton.DialogResult = [Windows.Forms.DialogResult]::Retry
    $dialog.Controls.Add($passwordButton)

    $cancelButton = [Windows.Forms.Button]::new()
    $cancelButton.Text = (T 'cancel')
    $cancelButton.Location = [Drawing.Point]::new(396, 174)
    $cancelButton.Size = [Drawing.Size]::new(100, 30)
    $cancelButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $dialog.Controls.Add($cancelButton)
    $dialog.AcceptButton = $classicButton
    $dialog.CancelButton = $cancelButton

    $answer = $dialog.ShowDialog()
    $dialog.Dispose()
    switch ($answer) {
        ([Windows.Forms.DialogResult]::Yes) { return $Addresses.ClassicUrl }
        ([Windows.Forms.DialogResult]::No)  { return $Addresses.SebanUrl }
        ([Windows.Forms.DialogResult]::Retry) { return 'panel-password' }
        default { return $null }
    }
}

$panelButton.Add_Click({
    $addresses = Get-M2PanelAddresses -ServerRoot $root
    $url = Show-PanelChoiceDialog -Addresses $addresses
    if ($url -eq 'panel-password') {
        Show-PanelPasswordDialog
        return
    }
    if ($url) {
        Write-LocalLog "Otwieram panel: $url"
        Start-Process $url
    }
})
$clientButton.Add_Click({ [void](Select-ClientExecutable) })
$updateButton.Add_Click({
    # One button for the whole flow: check in-process, and only offer to install
    # when there really is something newer.
    $installed = Get-InstalledServerVersion
    Write-LocalLog "Sprawdzam aktualizacje (zainstalowana wersja: $installed)..."
    $manifest = $null
    try {
        $config = Get-M2LauncherConfig -ServerRoot $root -ConfigPath $configPath
        $manifest = Get-M2UpdateManifest -Source ([string]$config.manifestUrl)
    }
    catch {
        Write-LocalLog "Nie udało się sprawdzić aktualizacji: $($_.Exception.Message)"
        [Windows.Forms.MessageBox]::Show(
            "Nie udało się sprawdzić aktualizacji.`r`n`r`n$($_.Exception.Message)",
            'Sprawdzanie aktualizacji', 'OK', 'Warning') | Out-Null
        return
    }
    $server = $null
    $serverProperty = $manifest.PSObject.Properties['server']
    if ($serverProperty -and $serverProperty.Value) { $server = $serverProperty.Value }
    if (-not $server -or -not [string]$server.version) {
        $message = 'Kanał aktualizacji nie podał wersji serwera. Twoja instalacja pozostaje bez zmian.'
        $statusProperty = $manifest.PSObject.Properties['statusMessage']
        if ($statusProperty -and [string]$statusProperty.Value) { $message = [string]$statusProperty.Value }
        Write-LocalLog $message
        [Windows.Forms.MessageBox]::Show($message, 'Brak aktualizacji', 'OK', 'Information') | Out-Null
        return
    }
    $available = ([string]$server.version).Trim()
    $script:latestManifest = $manifest
    $script:latestServerVersion = $available
    Set-LatestVersionsFromManifest -Manifest $manifest
    $script:latestVersionChecked = $true
    Update-VersionFooter
    Write-LocalLog "Dostępna wersja serwera: $available"
    if ($installed -and $installed -ne 'unknown' -and $installed.Equals($available, [StringComparison]::OrdinalIgnoreCase)) {
        [Windows.Forms.MessageBox]::Show("Masz już najnowszą wersję ($available).", 'Aktualizacje', 'OK', 'Information') | Out-Null
        return
    }
    $answer = [Windows.Forms.MessageBox]::Show(
        "Znaleziono nową wersję serwera: $available`r`n(zainstalowana: $installed)`r`n`r`nZainstalować teraz?`r`n`r`nTwoje postacie, przedmioty i boty pozostaną bez zmian. Aktualizacja przebudowuje serwer lokalnie — przy pierwszym razie może to potrwać kilkanaście–kilkadziesiąt minut. Postęp zobaczysz w logu poniżej.",
        'Dostępna aktualizacja', 'YesNo', 'Question')
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) {
        Write-LocalLog 'Aktualizacja odłożona na później.'
        return
    }
    # The server only. The client half of the GM panel is experimental and
    # goes in through its own button below, never with the ordinary update.
    Start-LauncherAction -Action 'UpdateServer' -Yes
})
$gmPanelButton.Add_Click({
    $config = Get-M2LauncherConfig -ServerRoot $root -ConfigPath $configPath
    if (-not [string]$config.clientRoot) {
        [Windows.Forms.MessageBox]::Show('Najpierw wskaż folder klienta przyciskiem WYBIERZ KLIENTA.', 'Brak klienta', 'OK', 'Information') | Out-Null
        return
    }
    if ($script:clientUpdateIsPlain) {
        $answer = [Windows.Forms.MessageBox]::Show(
            "Zaktualizować klienta w $($config.clientRoot)?`r`n`r`nPodmienia pack\root.index i pack\root.data (skrypty gry). Poprzednie wersje trafiają do backups\client w folderze serwera.",
            'Aktualizacja klienta', 'YesNo', 'Question')
        if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
        Start-LauncherAction -Action 'UpdateClient' -Yes
        return
    }
    $answer = [Windows.Forms.MessageBox]::Show(
        "Panel GM na F9 (autor: OskarPWA) to funkcja MOCNO EKSPERYMENTALNA.`r`n`r`nInstalacja podmienia w kliencie dwa pliki: packoot.eix i packoot.epk (skrypty gry). Poprzednie wersje trafiają do kopii zapasowej w folderze serwera (backups\client), więc da się wrócić.`r`n`r`nPanel otwiera tylko postać z uprawnieniami GM klawiszem F9. Jeśli po instalacji gra nie wczytuje się do końca, przywróć pliki z kopii i zgłoś to na Discordzie.`r`n`r`nZainstalować teraz?",
        'Panel GM F9 - wersja testowa', 'YesNo', 'Warning')
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
    Start-LauncherAction -Action 'UpdateClient' -Yes
})
$diagnosticsButton.Add_Click({ Start-LauncherAction -Action 'Diagnose' })
$bundleButton.Add_Click({
    # The support address comes from the update manifest, so it is looked up
    # once per session - a slow or missing network just falls back to the ZIP.
    $support = Get-SupportSettings
    if ($support.UploadUrl) {
        $answer = [Windows.Forms.MessageBox]::Show(
            "Spakowac logi i wyslac je od razu do autora projektu?`r`n`r`nPaczka zawiera logi Dockera i konfiguracje z usunietymi haslami.`r`n`r`nNIE = tylko zapisz ZIP na dysku.",
            'Wyslij logi', 'YesNoCancel', 'Question')
        if ($answer -eq [Windows.Forms.DialogResult]::Cancel) { return }
        if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
            Start-LauncherAction -Action 'SendLogs' -Yes
            return
        }
    }
    else {
        [Windows.Forms.MessageBox]::Show(
            "Zapisze paczke ZIP z logami i otworze jej folder - dolacz ja na Discordzie.`r`n`r`nOtworze tez zaproszenie na serwer.",
            'Logi', 'OK', 'Information') | Out-Null
        $script:openContactAfterAction = $support.ContactUrl
    }
    Start-LauncherAction -Action 'Logs' -OpenSupport
})
$openLogButton.Add_Click({
    if (-not (Test-Path -LiteralPath $sessionLog -PathType Leaf)) { Write-LocalLog 'Utworzono dziennik launchera.' }
    Start-Process notepad.exe -ArgumentList ('"{0}"' -f $sessionLog)
})
$folderButton.Add_Click({
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    Start-Process explorer.exe -ArgumentList ('"{0}"' -f $logDirectory)
})
$botCountButton.Add_Click({
    $current = Get-BotCountFromEnv
    $count = Show-BotCountDialog -Current $current
    if ($null -eq $count) { return }
    $answer = [Windows.Forms.MessageBox]::Show(
        "Ustawić $count grających botów i zrestartować serwer teraz, aby zastosować? Baza i postęp botów pozostaną bez zmian.",
        'Liczba botów', 'YesNoCancel', 'Question')
    if ($answer -eq [Windows.Forms.DialogResult]::Cancel) { return }
    if ($answer -eq [Windows.Forms.DialogResult]::Yes) {
        Start-LauncherAction -Action 'SetBots' -Yes -ExtraArgs @('-BotCount', "$count")
    }
    else {
        Start-LauncherAction -Action 'SetBots' -ExtraArgs @('-BotCount', "$count")
    }
})
$importDbButton.Add_Click({
    if (-not (Confirm-DockerReady)) { return }
    $target = Get-GuiTargetVolume
    $sources = @()
    try { $sources = @(Get-M2DbDataVolumes | Where-Object { $_.Name -ne $target }) } catch { $sources = @() }
    if (-not $sources -or $sources.Count -eq 0) {
        [Windows.Forms.MessageBox]::Show('Nie znaleziono innej bazy Docker do importu na tym komputerze.', 'Import bazy', 'OK', 'Information') | Out-Null
        return
    }
    $dlg = [Windows.Forms.Form]::new()
    $dlg.Text = (T 'importDialog')
    $dlg.Size = [Drawing.Size]::new(470, 320)
    $dlg.StartPosition = 'CenterParent'
    $dlg.FormBorderStyle = 'FixedDialog'
    $dlg.MaximizeBox = $false
    $dlg.MinimizeBox = $false
    $lbl = [Windows.Forms.Label]::new()
    $lbl.Text = (T 'importInfo')
    $lbl.Location = [Drawing.Point]::new(12, 10)
    $lbl.Size = [Drawing.Size]::new(430, 44)
    $dlg.Controls.Add($lbl)
    $list = [Windows.Forms.ListBox]::new()
    $list.Location = [Drawing.Point]::new(12, 58)
    $list.Size = [Drawing.Size]::new(430, 170)
    # The project names are opaque hashes, so the creation date is the only thing
    # that tells one install from another.
    foreach ($item in $sources) {
        $label = $item.Project
        if ($item.CreatedAt) { $label = '{0}   (utworzona {1:yyyy-MM-dd HH:mm})' -f $item.Project, $item.CreatedAt }
        [void]$list.Items.Add($label)
    }
    $list.SelectedIndex = 0
    $dlg.Controls.Add($list)
    $okButton = [Windows.Forms.Button]::new()
    $okButton.Text = (T 'importOk')
    $okButton.Location = [Drawing.Point]::new(246, 240)
    $okButton.Size = [Drawing.Size]::new(95, 32)
    $okButton.DialogResult = [Windows.Forms.DialogResult]::OK
    $dlg.Controls.Add($okButton)
    $cancelButton = [Windows.Forms.Button]::new()
    $cancelButton.Text = (T 'cancel')
    $cancelButton.Location = [Drawing.Point]::new(347, 240)
    $cancelButton.Size = [Drawing.Size]::new(95, 32)
    $cancelButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $dlg.Controls.Add($cancelButton)
    $dlg.AcceptButton = $okButton
    $dlg.CancelButton = $cancelButton
    $result = $dlg.ShowDialog()
    $picked = ''
    if ($list.SelectedIndex -ge 0) { $picked = [string]$sources[$list.SelectedIndex].Project }
    $dlg.Dispose()
    if ($result -ne [Windows.Forms.DialogResult]::OK -or -not $picked) { return }
    $confirm = [Windows.Forms.MessageBox]::Show(
        "Zaimportować świat z '$picked' do bieżącej instalacji?`r`n`r`nObecny świat zostanie ZASTĄPIONY (kopia trafi do folderu 'backups'), a serwer zostanie zatrzymany na czas importu. Źródło pozostanie nietknięte.",
        'Potwierdź import bazy', 'YesNo', 'Warning')
    if ($confirm -ne [Windows.Forms.DialogResult]::Yes) { return }
    Start-LauncherAction -Action 'ImportDb' -Yes -ExtraArgs @('-ImportSource', "$picked")
})
$worldBackupButton.Add_Click({
    # One button rather than three, because the main window has no room for
    # three and the report was that the backup could not be FOUND, not that it
    # was too many clicks away. The dialog says what each of them does before
    # anything is stopped or deleted.
    if (-not (Confirm-DockerReady)) { return }
    $dlg = [Windows.Forms.Form]::new()
    $dlg.Text = (T 'backupDialog')
    $dlg.Size = [Drawing.Size]::new(470, 300)
    $dlg.StartPosition = 'CenterParent'
    $dlg.FormBorderStyle = 'FixedDialog'
    $dlg.MaximizeBox = $false
    $dlg.MinimizeBox = $false
    $lbl = [Windows.Forms.Label]::new()
    $lbl.Text = (T 'backupInfo')
    $lbl.Location = [Drawing.Point]::new(12, 10)
    $lbl.Size = [Drawing.Size]::new(430, 60)
    $dlg.Controls.Add($lbl)
    $choice = ''
    $makeButton = [Windows.Forms.Button]::new()
    $makeButton.Text = (T 'backupMake')
    $makeButton.Location = [Drawing.Point]::new(12, 80)
    $makeButton.Size = [Drawing.Size]::new(430, 40)
    $makeButton.Add_Click({ $script:guiBackupChoice = 'make'; $dlg.DialogResult = [Windows.Forms.DialogResult]::OK })
    $dlg.Controls.Add($makeButton)
    $loadButton = [Windows.Forms.Button]::new()
    $loadButton.Text = (T 'backupLoad')
    $loadButton.Location = [Drawing.Point]::new(12, 126)
    $loadButton.Size = [Drawing.Size]::new(430, 40)
    $loadButton.Add_Click({ $script:guiBackupChoice = 'load'; $dlg.DialogResult = [Windows.Forms.DialogResult]::OK })
    $dlg.Controls.Add($loadButton)
    $resetButton = [Windows.Forms.Button]::new()
    $resetButton.Text = (T 'backupReset')
    $resetButton.Location = [Drawing.Point]::new(12, 172)
    $resetButton.Size = [Drawing.Size]::new(430, 40)
    $resetButton.BackColor = [Drawing.Color]::FromArgb(180, 75, 55)
    $resetButton.ForeColor = [Drawing.Color]::White
    $resetButton.Add_Click({ $script:guiBackupChoice = 'reset'; $dlg.DialogResult = [Windows.Forms.DialogResult]::OK })
    $dlg.Controls.Add($resetButton)
    $cancelButton = [Windows.Forms.Button]::new()
    $cancelButton.Text = (T 'cancel')
    $cancelButton.Location = [Drawing.Point]::new(347, 222)
    $cancelButton.Size = [Drawing.Size]::new(95, 30)
    $cancelButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
    $dlg.Controls.Add($cancelButton)
    $dlg.CancelButton = $cancelButton
    $script:guiBackupChoice = ''
    $result = $dlg.ShowDialog()
    $choice = $script:guiBackupChoice
    $dlg.Dispose()
    if ($result -ne [Windows.Forms.DialogResult]::OK -or -not $choice) { return }

    if ($choice -eq 'make') {
        Start-LauncherAction -Action 'BackupDb' -Yes
        return
    }
    if ($choice -eq 'load') {
        $backupRoot = Join-Path $root 'backups'
        if (-not (Test-Path -LiteralPath $backupRoot -PathType Container) -or
            -not (Get-ChildItem -LiteralPath $backupRoot -Filter 'db-backup-*.zip' -File -ErrorAction SilentlyContinue)) {
            [Windows.Forms.MessageBox]::Show((T 'backupNone'), (T 'backupDialog'), 'OK', 'Information') | Out-Null
            return
        }
        $picker = [Windows.Forms.OpenFileDialog]::new()
        $picker.Title = (T 'backupPick')
        $picker.InitialDirectory = $backupRoot
        $picker.Filter = 'Kopia swiata (db-backup-*.zip)|db-backup-*.zip|ZIP|*.zip'
        if ($picker.ShowDialog() -ne [Windows.Forms.DialogResult]::OK) { $picker.Dispose(); return }
        $file = $picker.FileName
        $picker.Dispose()
        $confirm = [Windows.Forms.MessageBox]::Show(
            "Przywrócić świat z '$([IO.Path]::GetFileName($file))'?`r`n`r`nObecny świat zostanie ZASTĄPIONY. Zanim to nastąpi, launcher zapisze go do własnej kopii w folderze 'backups', więc da się cofnąć.",
            'Potwierdź przywrócenie kopii', 'YesNo', 'Warning')
        if ($confirm -ne [Windows.Forms.DialogResult]::Yes) { return }
        Start-LauncherAction -Action 'RestoreDb' -Yes -ExtraArgs @('-RestoreSource', "$file")
        return
    }
    # reset
    $confirm = [Windows.Forms.MessageBox]::Show(
        "Zresetować świat do stanu świeżej instalacji?`r`n`r`nZniknie CAŁY obecny świat: postacie, poziomy, ekwipunek, boty i konta gry. Launcher najpierw zapisze go do kopii zip w folderze 'backups', więc da się do niego wrócić przyciskiem KOPIA SWIATA -> Przywroc swiat z kopii.`r`n`r`nPierwszy start po resecie potrwa dłużej - baza powstaje od nowa i boty są zasiewane.",
        'Potwierdź reset świata', 'YesNo', 'Warning')
    if ($confirm -ne [Windows.Forms.DialogResult]::Yes) { return }
    $again = [Windows.Forms.MessageBox]::Show(
        "Na pewno? To ostatnie pytanie.`r`n`r`nPo kliknięciu TAK obecny świat przestaje być światem tego serwera.",
        'Reset świata', 'YesNo', 'Warning')
    if ($again -ne [Windows.Forms.DialogResult]::Yes) { return }
    Start-LauncherAction -Action 'ResetWorld' -Yes
})
$dbAccessButton.Add_Click({
    # In-process on purpose: an action would print through the log box and the
    # launcher log, and the launcher log travels in support bundles. Read-only
    # text boxes so the values can be selected and copied.
    $envPath = Join-Path $root 'linux-port\docker\.env'
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        [Windows.Forms.MessageBox]::Show((T 'dbAccessNoEnv'), (T 'dbAccessTitle'), 'OK', 'Warning') | Out-Null
        return
    }
    $envText = [IO.File]::ReadAllText($envPath)
    $read = {
        param($name, $default)
        $m = [Regex]::Match($envText, "(?m)^$name=(.*?)\s*$")
        if ($m.Success -and $m.Groups[1].Value) { $m.Groups[1].Value } else { $default }
    }
    $rows = @(
        @('Host', '127.0.0.1'),
        @('Port', (& $read 'M2_DB_PUBLISH_PORT' '3306')),
        @('root', (& $read 'M2_DB_ROOT_PASSWORD' '')),
        @((& $read 'M2_DB_USER' 'metin2'), (& $read 'M2_DB_PASSWORD' ''))
    )
    $dlg = [Windows.Forms.Form]::new()
    $dlg.Text = (T 'dbAccessTitle')
    $dlg.Size = [Drawing.Size]::new(560, 372)
    $dlg.StartPosition = 'CenterParent'
    $dlg.FormBorderStyle = 'FixedDialog'
    $dlg.MaximizeBox = $false
    $dlg.MinimizeBox = $false
    $y = 18
    foreach ($row in $rows) {
        $label = [Windows.Forms.Label]::new()
        $label.Text = $row[0]
        $label.Location = [Drawing.Point]::new(18, $y + 4)
        $label.Size = [Drawing.Size]::new(110, 22)
        $dlg.Controls.Add($label)
        $box = [Windows.Forms.TextBox]::new()
        $box.Text = $row[1]
        $box.ReadOnly = $true
        $box.Location = [Drawing.Point]::new(132, $y)
        $box.Size = [Drawing.Size]::new(396, 24)
        $box.Font = [Drawing.Font]::new('Consolas', 9)
        $dlg.Controls.Add($box)
        $y += 34
    }
    $hint = [Windows.Forms.Label]::new()
    $hint.Text = (T 'dbAccessHint')
    if ($script:clientUpdateIsPlain) { $hint.Text = (T 'dbAccessHint') + [Environment]::NewLine + [Environment]::NewLine + (T 'dbAccessProtoNote') }
    $hint.Location = [Drawing.Point]::new(18, $y + 8)
    $hint.Size = [Drawing.Size]::new(510, 160)
    $dlg.Controls.Add($hint)
    $dlg.Size = [Drawing.Size]::new(560, 412)
    $openButton = [Windows.Forms.Button]::new()
    $openButton.Text = (T 'dbAccessOpenEnv')
    $openButton.Location = [Drawing.Point]::new(18, 330)
    $openButton.Size = [Drawing.Size]::new(170, 32)
    $openButton.Add_Click({ Start-Process notepad.exe -ArgumentList ('"' + $envPath + '"') }.GetNewClosure())
    $dlg.Controls.Add($openButton)
    $okButton = [Windows.Forms.Button]::new()
    $okButton.Text = 'OK'
    $okButton.Location = [Drawing.Point]::new(433, 330)
    $okButton.Size = [Drawing.Size]::new(95, 32)
    $okButton.DialogResult = [Windows.Forms.DialogResult]::OK
    $dlg.Controls.Add($okButton)
    $dlg.AcceptButton = $okButton
    $dlg.ShowDialog() | Out-Null
    $dlg.Dispose()
})
$repairDbButton.Add_Click({
    if (-not (Confirm-DockerReady)) { return }
    $answer = [Windows.Forms.MessageBox]::Show(
        "Naprawić dostęp do bazy?`r`n`r`nUżyj tego, gdy po imporcie serwer nie startuje (playerbot-migrate kończy się błędem) albo gdy Navicat/HeidiSQL odrzuca hasło z pliku .env. Odtwarza tylko techniczne konta bazy (gry i root) — postacie, przedmioty i boty pozostają BEZ ZMIAN. Serwer zostanie zatrzymany na czas naprawy.",
        'Napraw dostęp do bazy', 'YesNo', 'Question')
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) { return }
    Start-LauncherAction -Action 'RepairDb'
})

$timer = [Windows.Forms.Timer]::new()
$timer.Interval = 1200
$timer.Add_Tick({ Update-ActionStream; Complete-LauncherAction })
$timer.Start()

$statusTimer = [Windows.Forms.Timer]::new()
$statusTimer.Interval = 8000
$statusTimer.Add_Tick({
    if ($script:activeProcess) { return }
    Refresh-Status
    # One manifest read per session: on the first quiet tick rather than during
    # form startup, so the window is already usable while it happens.
    Read-LatestServerVersion
})
$statusTimer.Start()

$script:form.Add_FormClosing({
    param($sender, $eventArgs)
    if ($script:activeProcess -and -not $script:activeProcess.HasExited) {
        $answer = [Windows.Forms.MessageBox]::Show(
            'Launcher nadal wykonuje operację. Czy na pewno zamknąć okno?',
            'Operacja w toku', 'YesNo', 'Warning')
        if ($answer -ne [Windows.Forms.DialogResult]::Yes) { $eventArgs.Cancel = $true }
    }
})

if (Test-Path -LiteralPath $sessionLog -PathType Leaf) {
    $tail = Get-Content -LiteralPath $sessionLog -Tail 12 -ErrorAction SilentlyContinue
    if ($tail) { $script:logBox.Text = ($tail -join [Environment]::NewLine) + [Environment]::NewLine }
}
Write-LocalLog 'Uruchomiono GUI launchera.'
Update-VersionFooter
Refresh-Status
[void]$script:form.ShowDialog()
