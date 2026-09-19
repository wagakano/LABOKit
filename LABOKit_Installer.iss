[Setup]
AppName=LABOKit
AppVersion=3.3.2
DefaultDirName={autopf}\LABOKit
DefaultGroupName=LABOKit
UninstallDisplayIcon={app}\LABOKit.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=LABOKit_v3.3.2_Setup
SetupIconFile=labokit.ico
PrivilegesRequired=lowest

[Files]
Source: "dist\LABOKit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LABOKit"; Filename: "{app}\LABOKit.exe"; IconFilename: "{app}\LABOKit.exe"
Name: "{autodesktop}\LABOKit"; Filename: "{app}\LABOKit.exe"; IconFilename: "{app}\LABOKit.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\LABOKit.exe"; Description: "Launch LABOKit"; Flags: nowait postinstall skipifsilent
