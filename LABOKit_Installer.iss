#ifndef ReleasePayload
  #define ReleasePayload "dist\LABOKit"
#endif
#ifndef ReleaseOutput
  #define ReleaseOutput "dist"
#endif

[Setup]
AppName=LABOKit
AppId=LABOKit
AppVersion=3.3.2
VersionInfoVersion=3.3.2.0
DefaultDirName={autopf}\LABOKit
DefaultGroupName=LABOKit
UninstallDisplayIcon={app}\LABOKit.exe
Compression=lzma2/fast
SolidCompression=yes
OutputDir={#ReleaseOutput}
OutputBaseFilename=LABOKit_v3.3.2_Setup
SetupIconFile=labokit.ico
PrivilegesRequired=lowest

[Files]
Source: "{#ReleasePayload}\*"; DestDir: "{app}"; Excludes: "\_internal\plugins\QuickVector.kit,\_internal\plugins\DitheringFX.kit,\_internal\plugins\IMGConverter.kit"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LABOKit"; Filename: "{app}\LABOKit.exe"; IconFilename: "{app}\LABOKit.exe"
Name: "{autodesktop}\LABOKit"; Filename: "{app}\LABOKit.exe"; IconFilename: "{app}\LABOKit.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\LABOKit.exe"; Description: "Launch LABOKit"; Flags: nowait postinstall skipifsilent
