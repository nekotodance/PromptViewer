## About PromptViewer 0.1.3
PromptViewer is a tool designed to easily sort images created with StableDiffusion into a specified folder while checking the prompt information.  
Using a mouse or keyboard, you can quickly and easily preview and sort with only one hand!  
Supports display of jpg, png, and webp files  
![PromptViewer-image](docs/PromptViewer-image001.jpg)

## How to install (simplified)
[Download simplified installation zip] https://github.com/nekotodance/PromptViewer/releases/download/latest/PromptViewer.zip

- Extract the zip file  
- Right-click “pv-install.ps1” in the extracted folder and select “Run with PowerShell  
- At the end of the install, it will ask if you want to copy the link to your desktop  
At the end of the install, it will ask if you want to copy the link to your desktop.  
Type “y” if you want to, or just press “enter”.  
If not necessary, type “n” and press “enter  
- A PromptViewer link will be created.  

Double-click on the link file, or drag & drop an image directly into the link file to launch PromptViewer.  

## How to install (manually)
The installation method is explained in the case that the installation folder is C:\tool\git\PromptViewer  
It is assumed that Python is installed and you have minimum knowledge of Python!  

#### 1)Create C:\tool\git\PromptViewer
#### 2)Store the following files
  PromptViewer.py  
  PromptViewer_beep.wav  
  PromptViewer_filecansel.wav  
  PromptViewer_filecopyok.wav  
  PromptViewer_filemoveok.wav  
  PromptViewer_moveend.wav  
  PromptViewer_movetop.wav  
  pvsubfunc.py  
  
  PromptViewer_settings.json *1  

*1:The settings file is automatically created if you do not have one, so it is not necessary.  
  
#### 3) Launch a command prompt and execute the following. This procedure is only once for installation
###### 3-1) Move current folder Move
    c: cd
    cd C:\tool\git\PromptViewer
###### 3-2)Create venv environment, activate
    py -m venv venv
    . \venv\Scripts\activate.bat
###### 3-3)Install the libraries to be used
    pip install PyQt5 pyperclip Image
###### 3-4) Check the operation
    py PromptViewer.py
    
###### 3-5)Change settings
To change the configuration file, refer to “About the Configuration File”! Refer to “About configuration files” and change image-fcopy-dir and image-fmove-dir!  

#### 4) Create a convenient shortcut for starting up
  Right-click on the appropriate folder and select “New”->"Shortcut  
Enter the following in “Item location...” Enter the following in
  C:\tool\git\PromptViewer\Scripts\pythonw.exe C:\tool\git\PromptViewer\PromptViewer.py  
  
  From now on, you can use the created shortcut as if it were an app by double-clicking on it!  
  You can also drag and drop files (or folders with images) to this shortcut.  

## About the configuration file
PromptViewer_settings.json contains the following information  
! Especially, image-fcopy-dir and image-fmove-dir should be rewritten [be sure to change them according to your environment]!  

image-fcopy-dir : W, the name of the folder to which files are copied using the up key  
image-fmove-dir : S, the name of the folder to which files are moved using the down key (note that this is a file move)  

info-label-w : width of Prompt display area (default value: 480)  
geometry-x,y : last window position  
geometry-w,h : last window size  

The following are sound effects (you can change the WAVE file to anything you like, though I haven't tried it)  
sound-beep : Error on when processing fails  
sound-fcopy-ok : sound when copy succeeded  
sound-fmove-ok : sound on successful move  
sound-f-cansel : sound when copy or move is canceled  
sound-move-top : sound when the next image is displayed and the image goes back to the first image.  
sound-move-end : sound when the previous image is displayed and the user goes back to the last image.  

## How to use
Drag and drop an image file (JPG or PNG file) or a folder containing image files onto the application.  
Drag and drop to the shortcut created in step 4) of the installation will also work.  
Or, you can specify an image file or a folder containing images as an argument when executing Python.  

#### Key operation (If you want to change the assignment, please rewrite the key event processing in the source as you like)
AD, Left/Right : Move to the next/previous image in the same folder  
Q,ESC : Exit  
0,1,2 : Fits the image to 0:1/2, 1:Equal size, 2:2 times the image size (toggle operation)  
F,Enter : Switch to full screen display (toggle action)  
W,Top : Copy the displayed image to the folder specified by “image-fcopy-dir” in the setting file *2  
S,Down : Move the displayed image to the folder specified by “image-fmove-dir” in the configuration file *3  
K : Seed number to copy buffer *4  
P : Prompt string to copy buffer *4  
N : Negative Prompt string to copy buffer *4  
H : Hires Prompt string to copy buffer *4  

#### Mouse operation
Wheel operation : move to the next/previous image in the same folder  
Right click : Copy the displayed image to the folder specified by image-fcopy-dir in the configuration file *2  
Double left click : Toggle full screen display (toggle operation)  
Left drag : Move the window  

*2: Copying can be canceled (deleted from the destination) by pressing the key again.  
*3: Move can be canceled by pressing the key again (only possible when not moving from the image).  
*4: ComfyUI output files are not supported.  

## Screen Display
![PromptViewer-image](docs/PromptViewer-image002.jpg)

#### Window Title
Full path file name of [number of currently displayed image/total number of images in the same folder].  

#### Prompt Info
Display the text in different colors and thicknesses as follows
- Gray : Prompt  
- Purple : Negative Prompt  
- Green : Hires Prompt  
- Yellow Bold : Lora Name  
- Light blue bold : Seed number  
- Bold orange : Model name  
- Orange : Colorize text ADetailer prompt, Steps:, steps:  

*Output files from ComfyUI are only partially supported.  

#### Status Bar
Display of operation status

## Notes.
- We have checked the display in the output files of Automatic1111, Forge, reForge, and ComfyUI*  
*However, ComfyUI varies from node to node and is not guaranteed to be displayed.)  
- Currently, line feed codes in the Prompt information are not picked up properly in png files, which may indicate a problem with the Image library or the character encoding.  
- ComfyUI does not support copying or coloring of Prompt information.  

## Changelog
- 0.1.3 Support for displaying webp files following jpg and png  
- 0.1.2 Added support for coloring and line breaks in the text portion of ComfyUI PNG files (tentative)  
- 0.1.1 When exiting while in full screen, exit after canceling full screen (to avoid saving strange screen sizes).  
- 0.1.0 Various fixes, but this is the first version.  
