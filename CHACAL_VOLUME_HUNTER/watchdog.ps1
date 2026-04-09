param(
  [string]$ContainerName = 'chacal_volume_dryrun',
  [string]$LogFile = 'watchdog.log'
)

function Send-TelegramMessage($text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return }
  $token = '8760247299:AAHNhw7k-YlEG2kL7lO0Ze5cbuRzg7y8bW4'
  $chatId = '6527908321'
  $encoded = [System.Uri]::EscapeDataString($text)
  $url = "https://api.telegram.org/bot$token/sendMessage?chat_id=$chatId&text=$encoded"
  try {
    Invoke-RestMethod -Uri $url -UseBasicParsing | Out-Null
  } catch {
    Write-Output "[watchdog] fallo al avisar por Telegram: $_"
  }
}

function Test-Internet {
  for ($i = 0; $i -lt 3; $i++) {
    if (Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet) {
      return $true
    }
    Start-Sleep -Seconds 5
  }
  return $false
}

while ($true) {
  $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

  $internet = Test-Internet
  if (-not $internet) {
    $msg = "[$timestamp] Sin internet. Esperando 30s antes de reintentar..."
    Add-Content $LogFile $msg
    Send-TelegramMessage $msg
    Start-Sleep -Seconds 30
    continue
  }

  $container = docker ps --filter "name=$ContainerName" --filter "status=running" --format '{{.Names}}'
  if (-not $container) {
    $msg = "[$timestamp] Contenedor $ContainerName no estaba levantado. Reiniciando..."
    Add-Content $LogFile $msg
    Send-TelegramMessage $msg
    & "${PSScriptRoot}\start.cmd"
    Add-Content $LogFile "[$timestamp] Reinicio solicitado."
    Start-Sleep -Seconds 60
    continue
  }

  $msg = "[$timestamp] Bot activo. Internet OK."
  Add-Content $LogFile $msg
  Send-TelegramMessage $msg
  Start-Sleep -Seconds 180
}