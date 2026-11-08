$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "Video Subtitle Studio.lnk"
$TargetExe = "D:\CODE\videoTranslator\dist\VideoSubtitleStudio.exe"
$IconFile = "D:\CODE\videoTranslator\assets\icon.ico"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetExe
$Shortcut.WorkingDirectory = "D:\CODE\videoTranslator"
$Shortcut.IconLocation = $IconFile
$Shortcut.Description = "Video Soft-Sub Scraper & Translator Studio"
$Shortcut.Save()

if (Test-Path $ShortcutPath) {
    Write-Host "[SUCCESS] Shortcut desktop berhasil dibuat di: $ShortcutPath"
} else {
    Write-Host "[!] Gagal membuat shortcut."
}
