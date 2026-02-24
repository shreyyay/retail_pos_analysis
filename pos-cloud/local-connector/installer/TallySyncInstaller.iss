; Inno Setup 6 script for TallySync Installer
; Build with: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" TallySyncInstaller.iss
; (run from the installer\ directory, after building both PyInstaller exes)

#define MyAppName      "TallySync"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "Your Business Name"
#define MyAppURL       "https://your-domain.com"
#define MyDistDir      "..\dist"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Require admin so Task Scheduler entries can be created
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=TallySyncInstaller
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TallySyncSetup\TallySyncSetup.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut for 'Run Sync Now'"; GroupDescription: "Additional icons:"

[Files]
; Main sync executable directory
Source: "{#MyDistDir}\tally_sync\*"; DestDir: "{app}\tally_sync"; Flags: ignoreversion recursesubdirs createallsubdirs

; Setup wizard executable directory
Source: "{#MyDistDir}\TallySyncSetup\*"; DestDir: "{app}\TallySyncSetup"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Run Sync Now";    Filename: "{app}\tally_sync\tally_sync.exe"
Name: "{group}\Setup TallySync"; Filename: "{app}\TallySyncSetup\TallySyncSetup.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TallySync — Run Now"; Filename: "{app}\tally_sync\tally_sync.exe"; Tasks: desktopicon

[Run]
; Launch the setup wizard automatically after installation finishes
Filename: "{app}\TallySyncSetup\TallySyncSetup.exe"; \
  Description: "Configure TallySync (recommended)"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove all 3 scheduled tasks on uninstall
Filename: "schtasks"; Parameters: "/delete /tn TallySync_11AM /f"; Flags: runhidden; RunOnceId: "DelTask11AM"
Filename: "schtasks"; Parameters: "/delete /tn TallySync_3PM  /f"; Flags: runhidden; RunOnceId: "DelTask3PM"
Filename: "schtasks"; Parameters: "/delete /tn TallySync_6PM  /f"; Flags: runhidden; RunOnceId: "DelTask6PM"

[Code]
// Warn if Tally is not running on port 9000
procedure CurPageChanged(CurPageID: Integer);
begin
  // Nothing needed — setup wizard handles all configuration
end;
