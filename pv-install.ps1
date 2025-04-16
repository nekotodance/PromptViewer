#---- アプリごとに固有の部分 ----
$appdispname = "Prompt Viewer"
$appfilename = "PromptViewer"
$iconfilename = "res\" + $appfilename + ".ico"
#---- アプリごとに固有の部分 ----

$folder = Split-Path -Parent $MyInvocation.MyCommand.Definition
$iconFile = Join-Path $folder $iconfilename
$arguments = $appfilename + ".py"
$shortcutName = $appfilename + ".lnk"
$workingDirectory = $folder
$shortcutPath = Join-Path $folder $shortcutName
$exeFile = Join-Path $folder "venv\Scripts\pythonw.exe"

Write-Host "========================================"
Write-Host $appdispname
Write-Host "install start."
Write-Host "========================================"

Write-Host "----------------------------------------"
Write-Host "create python venv."
Write-Host "----------------------------------------"
# create python venv
python -m venv venv

Write-Host "install python library."
Write-Host $pythonlibs
Write-Host "----------------------------------------"
# activate
. .\venv\Scripts\activate.ps1
# install python library
python -m pip install -r requirements.txt

Write-Host "----------------------------------------"
Write-Host "create shortcut file."
# make shortcutfile
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exeFile
$shortcut.Arguments = $arguments
if (Test-Path $iconFile) {
    $shortcut.IconLocation = $iconFile
} else {
    Write-Host "icon file not exist."
}
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.Save()
Write-Host "----------------------------------------"

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
