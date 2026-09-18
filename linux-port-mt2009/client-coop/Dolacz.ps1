# Metin2 SinglePlayer - dołączenie do świata znajomego (COOP, eksperymentalne).
#
# Znajomy, który hostuje świat, daje kod zaproszenia (M2COOP1:...). Ten plik
# leży w folderze klienta, zapisuje obok niego coop.cfg i nic więcej: klient
# czyta go przy starcie (serverinfo.py) i pokazuje świat znajomego jako drugi
# serwer na liście, "Online: <nazwa>". Kod niesie też login i hasło konta,
# które znajomy założył w swoim świecie - pokazujemy je, nigdzie nie zapisujemy.
#
# Samodzielny: na komputerze gracza, który tylko dołącza, nie ma serwera ani
# launchera, więc ten plik nie importuje niczego. Kod zaproszenia czyta tak
# samo jak launcher\Metin2Launcher.Coop.psm1 (Read-M2CoopInvite) i zapisuje
# coop.cfg tak samo jak Write-M2CoopClientConfig.
param([string]$Invite = '', [switch]$NoWindow)
$ErrorActionPreference = 'Stop'
$clientDir = $PSScriptRoot
$prefix = 'M2COOP1:'

function Read-CoopInvite {
    param([Parameter(Mandatory = $true)][string]$Code)
    $text = ($Code -replace '\s', '')
    if (-not $text.StartsWith($prefix)) { throw 'To nie jest kod zaproszenia (powinien zaczynać się od M2COOP1:).' }
    $b64 = $text.Substring($prefix.Length).Replace('-', '+').Replace('_', '/')
    switch ($b64.Length % 4) { 2 { $b64 += '==' } 3 { $b64 += '=' } }
    try { $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64)) }
    catch { throw 'Kod zaproszenia jest uszkodzony - skopiuj go jeszcze raz w całości.' }
    try { $invite = $json | ConvertFrom-Json } catch { throw 'Kod zaproszenia jest uszkodzony - skopiuj go jeszcze raz w całości.' }
    if ([string]$invite.host -notmatch '^[A-Za-z0-9.-]{1,253}$') { throw 'Kod zaproszenia: zły adres serwera.' }
    foreach ($field in @('auth', 'channel')) {
        $v = [int]$invite.$field
        if ($v -le 0 -or $v -ge 65536) { throw "Kod zaproszenia: zły port ($field)." }
    }
    return $invite
}

function Write-CoopConfig {
    param([Parameter(Mandatory = $true)]$Invite)
    # The client reads coop.cfg as ASCII; a Polish letter becomes its plain
    # one rather than vanishing ("Swiat", not "wiat").
    $plain = [string]$Invite.name
    $pairs = @{ [char]0x0105 = 'a'; [char]0x0107 = 'c'; [char]0x0119 = 'e'; [char]0x0142 = 'l'; [char]0x0144 = 'n'; [char]0x00F3 = 'o'
        [char]0x015B = 's'; [char]0x017A = 'z'; [char]0x017C = 'z'; [char]0x0104 = 'A'; [char]0x0106 = 'C'; [char]0x0118 = 'E'
        [char]0x0141 = 'L'; [char]0x0143 = 'N'; [char]0x00D3 = 'O'; [char]0x015A = 'S'; [char]0x0179 = 'Z'; [char]0x017B = 'Z' }
    foreach ($k in $pairs.Keys) { $plain = $plain.Replace([string]$k, $pairs[$k]) }
    $name = ($plain -replace '[^\x20-\x7e]', '')
    if (-not $name) { $name = [string]$Invite.host }
    $channels = [int]$Invite.channels
    if ($channels -lt 1) { $channels = 1 }
    $lines = @(
        '# Metin2 SinglePlayer - swiat znajomego (zapisal Dolacz.ps1, kod zaproszenia)',
        ('name=' + $name),
        ('host=' + [string]$Invite.host),
        ('auth=' + [int]$Invite.auth),
        ('channel=' + [int]$Invite.channel),
        ('channels=' + $channels)
    )
    $path = Join-Path $clientDir 'coop.cfg'
    [IO.File]::WriteAllText($path, (($lines -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)
    return $path
}

if ($NoWindow) {
    if (-not $Invite) { $Invite = Read-Host 'Wklej kod zaproszenia' }
    $inv = Read-CoopInvite -Code $Invite
    $path = Write-CoopConfig -Invite $inv
    Write-Host ("Zapisano {0}" -f $path)
    Write-Host ("W kliencie wybierz serwer 'Online: {0}'. Login: {1}, hasło: {2}" -f $inv.name, $inv.login, $inv.password)
    return
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()

$form = [Windows.Forms.Form]::new()
$form.Text = 'Metin2 SinglePlayer - dołącz do świata znajomego'
$form.Size = [Drawing.Size]::new(600, 470)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false

$info = [Windows.Forms.Label]::new()
$info.Text = ('1. Wklej poniżej kod zaproszenia od znajomego (zaczyna się od M2COOP1:).' + [Environment]::NewLine +
    '2. Kliknij Dołącz - świat znajomego pojawi się w grze jako drugi serwer, "Online".' + [Environment]::NewLine +
    '3. Uruchom grę, wybierz ten serwer i zaloguj się loginem i hasłem, które pokażę.')
$info.Location = [Drawing.Point]::new(14, 12)
$info.Size = [Drawing.Size]::new(560, 56)
$form.Controls.Add($info)

$codeBox = [Windows.Forms.TextBox]::new()
$codeBox.Multiline = $true
$codeBox.WordWrap = $true
$codeBox.ScrollBars = 'Vertical'
$codeBox.Location = [Drawing.Point]::new(14, 74)
$codeBox.Size = [Drawing.Size]::new(556, 96)
$codeBox.Font = [Drawing.Font]::new('Consolas', 9)
$form.Controls.Add($codeBox)
try {
    $clip = [Windows.Forms.Clipboard]::GetText()
    if ($clip -and $clip.Trim().StartsWith($prefix)) { $codeBox.Text = $clip.Trim() }
}
catch { }

$joinButton = [Windows.Forms.Button]::new()
$joinButton.Text = 'Dołącz'
$joinButton.Location = [Drawing.Point]::new(14, 180)
$joinButton.Size = [Drawing.Size]::new(150, 36)
$joinButton.Font = [Drawing.Font]::new('Segoe UI Semibold', 10)
$form.Controls.Add($joinButton)

$result = [Windows.Forms.TextBox]::new()
$result.Multiline = $true
$result.ReadOnly = $true
$result.Location = [Drawing.Point]::new(14, 228)
$result.Size = [Drawing.Size]::new(556, 110)
$result.Font = [Drawing.Font]::new('Consolas', 10)
$form.Controls.Add($result)

$playButton = [Windows.Forms.Button]::new()
$playButton.Text = 'Uruchom grę'
$playButton.Location = [Drawing.Point]::new(14, 350)
$playButton.Size = [Drawing.Size]::new(150, 36)
$playButton.Enabled = $false
$form.Controls.Add($playButton)

$forgetButton = [Windows.Forms.Button]::new()
$forgetButton.Text = 'Usuń świat znajomego z listy'
$forgetButton.Location = [Drawing.Point]::new(176, 350)
$forgetButton.Size = [Drawing.Size]::new(220, 36)
$form.Controls.Add($forgetButton)

$closeButton = [Windows.Forms.Button]::new()
$closeButton.Text = 'Zamknij'
$closeButton.Location = [Drawing.Point]::new(470, 350)
$closeButton.Size = [Drawing.Size]::new(100, 36)
$closeButton.DialogResult = [Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($closeButton)
$form.CancelButton = $closeButton

$existing = Join-Path $clientDir 'coop.cfg'
if (Test-Path -LiteralPath $existing -PathType Leaf) {
    $text = [IO.File]::ReadAllText($existing)
    if ($text -match '(?m)^name=(.*)$') {
        $result.Text = ("W kliencie jest już świat znajomego: {0}.`r`nNowy kod go zastąpi." -f $Matches[1].Trim())
        $playButton.Enabled = $true
    }
}

$joinButton.Add_Click({
    try {
        $inv = Read-CoopInvite -Code $codeBox.Text
        [void](Write-CoopConfig -Invite $inv)
        try { [Windows.Forms.Clipboard]::SetText([string]$inv.password) } catch { }
        $result.Text = ("Gotowe. W grze wybierz serwer 'Online: {0}'.`r`n`r`nLogin: {1}`r`nHasło: {2}`r`n(hasło jest też w schowku)" -f $inv.name, $inv.login, $inv.password)
        $playButton.Enabled = $true
    }
    catch {
        [Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Kod zaproszenia', 'OK', 'Warning') | Out-Null
    }
})

$playButton.Add_Click({
    $exe = Join-Path $clientDir 'metin2client.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        [Windows.Forms.MessageBox]::Show('Nie ma metin2client.exe obok tego pliku.', 'Uruchom grę', 'OK', 'Warning') | Out-Null
        return
    }
    Start-Process -FilePath $exe -WorkingDirectory $clientDir | Out-Null
    $form.Close()
})

$forgetButton.Add_Click({
    if (Test-Path -LiteralPath $existing -PathType Leaf) { [IO.File]::Delete($existing) }
    $result.Text = 'Świat znajomego usunięty z listy serwerów.'
    $playButton.Enabled = $false
})

[void]$form.ShowDialog()
