#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{4CBFF2E8-B434-4142-B40A-116B728737DB}
AppName=TOMS SLA MN
AppVersion={#MyAppVersion}
AppPublisher=cuongtm88-blip
DefaultDirName={localappdata}\Programs\TOMS SLA MN
DefaultGroupName=TOMS SLA MN
PrivilegesRequired=lowest
OutputDir=dist-installer
OutputBaseFilename=TOMS-SLA-MN
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\TOMS-SLA-MN.exe

[Files]
Source: "dist\TOMS-SLA-MN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\TOMS SLA MN"; Filename: "{app}\TOMS-SLA-MN.exe"
Name: "{autodesktop}\TOMS SLA MN"; Filename: "{app}\TOMS-SLA-MN.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình"; GroupDescription: "Biểu tượng bổ sung:"; Flags: checkedonce

[Run]
Filename: "{app}\TOMS-SLA-MN.exe"; Description: "Mở TOMS SLA MN"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ReadyFile: String;
begin
  ReadyFile := GetEnv('TOMS_UPDATE_READY_FILE');
  if ReadyFile <> '' then
    SaveStringToFile(ReadyFile, 'installer-ready', False);
  Result := True;
end;
