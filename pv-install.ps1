Write-Host "========================================"
Write-Host "Prompt Viewer"
Write-Host "install start."
Write-Host "========================================"

$folder = Split-Path -Parent $MyInvocation.MyCommand.Definition
$exeFile = Join-Path $folder "venv\Scripts\pythonw.exe"
$arguments = "PromptViewer.py"
$iconFile = Join-Path $folder "res\PromptViewer.ico"
$workingDirectory = $folder
$shortcutName = "PromptViewer.lnk"
$shortcutPath = Join-Path $folder $shortcutName

# check if a shortcut already exists
if (Test-Path $shortcutPath) {
    Write-Host "========================================"
    Write-Host "already exists '$shortcutName'."
    Write-Host "Press any key to exit..."
    Write-Host "========================================"
    [void][System.Console]::ReadKey()
    exit
}

Write-Host "----------------------------------------"
Write-Host "create python venv."
Write-Host "----------------------------------------"
# create python venv
python -m venv venv

Write-Host "install python library."
Write-Host "----------------------------------------"
# activate
. .\venv\Scripts\activate.ps1
# install python library
python -m pip install PyQt5 pyperclip Image

Write-Host "----------------------------------------"
Write-Host "create shortcut file."
Write-Host "----------------------------------------"
# make shortcutfile
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exeFile
$shortcut.Arguments = $arguments
$shortcut.IconLocation = $iconFile
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.Save()

$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$desktopShortcutPath = Join-Path $desktopPath $shortcutName

# Check before copying shortcuts to the desktop
$copyConfirmation = Read-Host "Do you want to copy the shortcut to your desktop? (y or enter/n)"

Write-Host "----------------------------------------"
if ($copyConfirmation -eq "y" -or $copyConfirmation -eq "") {
    Copy-Item -Path $shortcutPath -Destination $desktopShortcutPath
    Write-Host "copied shortcut to desktop."
} else {
    Write-Host "canceled."
}
Write-Host "========================================"
Write-Host "install complete!!"
Write-Host "Press any key to exit..."
Write-Host "========================================"
[void][System.Console]::ReadKey()
