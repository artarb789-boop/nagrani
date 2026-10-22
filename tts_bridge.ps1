# Мост «На грани» -> Tabletop Simulator, версия 3 (git)
# Раз в несколько секунд забирает изменения из GitHub в эту папку.
# Изменённые файлы live\*.lua сразу выполняются в игре.
# Если обновился NaGrani.json, он копируется в сохранения TTS.
$Repo = "https://github.com/artarb789-boop/nagrani.git"
$Branch = "main"
$PollSeconds = 5
$Root = $PSScriptRoot
Set-Location $Root
$Host.UI.RawUI.WindowTitle = "Мост TTS — На грани (git)"
function Stamp() { Get-Date -Format "HH:mm:ss" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "Не найден Git. Установи Git for Windows: https://git-scm.com/download/win и запусти мост снова." -ForegroundColor Red
  return
}

function Send-TTS($code) {
  $json = @{ messageID = 3; guid = "-1"; script = $code } | ConvertTo-Json -Depth 5 -Compress
  $client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 39999)
  $stream = $client.GetStream()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
  $stream.Write($bytes, 0, $bytes.Length); $stream.Flush(); $client.Close()
}

# --- первый запуск: превращаем папку в копию репозитория ---
if (-not (Test-Path (Join-Path $Root ".git"))) {
  Write-Host "Первый запуск: подключаю папку $Root к GitHub..." -ForegroundColor Yellow
  Write-Host "Если откроется окно входа в GitHub, войди в свой аккаунт." -ForegroundColor Yellow
  git init -q
  git remote add origin $Repo
  git fetch -q origin $Branch
  if ($LASTEXITCODE -ne 0) { Write-Host "Не удалось скачать репозиторий. Проверь вход в GitHub." -ForegroundColor Red; return }
  git reset -q --hard "origin/$Branch"
  git branch -q -M $Branch
  git branch -q --set-upstream-to="origin/$Branch" $Branch
  Write-Host "Готово: папка совпадает с репозиторием." -ForegroundColor Green
}

$Saves = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "My Games\Tabletop Simulator\Saves"
function Copy-Save {
  if (Test-Path $Saves) {
    Copy-Item (Join-Path $Root "NaGrani.json") $Saves -Force
    Copy-Item (Join-Path $Root "NaGrani.png") $Saves -Force
    Write-Host ("{0}  Стол обновлён в сохранениях TTS. Перезагрузи его: Save & Load → «На грани»." -f (Stamp)) -ForegroundColor Yellow
  } else {
    Write-Host "Не нашёл папку сохранений TTS: $Saves" -ForegroundColor Red
  }
}

# --- ответы TTS ---
$listener = $null
try {
  $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 39998)
  $listener.Start()
} catch {
  Write-Host "Порт 39998 занят (может быть, открыт VS Code с плагином TTS). Ответы игры показываться не будут." -ForegroundColor Yellow
  $listener = $null
}

Write-Host "Мост v3 запущен. Проверяю GitHub каждые $PollSeconds с." -ForegroundColor Green
Write-Host "Окно не закрывай, пока играешь. Остановить: Ctrl+C."
$warned = $false
$nextPoll = Get-Date
while ($true) {
  if ((Get-Date) -ge $nextPoll) {
    $nextPoll = (Get-Date).AddSeconds($PollSeconds)
    git fetch -q origin $Branch 2>$null
    if ($LASTEXITCODE -ne 0) {
      if (-not $warned) { Write-Host ("{0}  Нет связи с GitHub, пробую дальше..." -f (Stamp)) -ForegroundColor Red; $warned = $true }
    } else {
      $warned = $false
      $local = (git rev-parse HEAD).Trim()
      $remote = (git rev-parse "origin/$Branch").Trim()
      if ($local -ne $remote) {
        $changed = @(git -c core.quotepath=false diff --name-only $local $remote)
        $msg = (git log -1 --format=%s $remote)
        git reset -q --hard "origin/$Branch"
        Write-Host ("{0}  Пришло обновление: {1}" -f (Stamp), $msg) -ForegroundColor Cyan
        foreach ($f in $changed) {
          $path = Join-Path $Root $f
          if ($f -like "live/*.lua" -and (Test-Path $path)) {
            $code = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
            try { Send-TTS $code; Write-Host ("{0}  -> выполнено в игре: {1}" -f (Stamp), $f) -ForegroundColor Cyan }
            catch { Write-Host ("{0}  {1} не отправлен: TTS не отвечает. Игра запущена и стол загружен?" -f (Stamp), $f) -ForegroundColor Red }
          }
        }
        if ($changed -contains "NaGrani.json") { Copy-Save }
        if ($changed -contains "tts_bridge.ps1") { Write-Host "Мост обновился. Закрой окно и запусти его снова." -ForegroundColor Yellow }
      }
    }
  }
  if ($listener -ne $null -and $listener.Pending()) {
    $c = $listener.AcceptTcpClient()
    $reader = New-Object System.IO.StreamReader($c.GetStream(), [System.Text.Encoding]::UTF8)
    $m = $reader.ReadToEnd(); $c.Close()
    try {
      $j = $m | ConvertFrom-Json
      if ($j.messageID -eq 2) { Write-Host ("TTS: " + $j.message) }
      elseif ($j.messageID -eq 3) { Write-Host ("ОШИБКА в игре: " + $j.error) -ForegroundColor Red }
    } catch { }
  }
  Start-Sleep -Milliseconds 400
}
