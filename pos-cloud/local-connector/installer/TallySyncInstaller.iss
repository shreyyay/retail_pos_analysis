; Inno Setup 6 script for TallySync Installer
; Build with: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" TallySyncInstaller.iss
; (run from the installer\ directory, after building all three PyInstaller exes)

#define MyAppName      "TallySync"
#define MyAppVersion   "1.1.0"
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
; Require admin so Task Scheduler entries can be created by the setup wizard
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=TallySyncInstaller
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TallySyncSetup\TallySyncSetup.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; ── Tally sync exe (reads sales from Tally, pushes to Supabase cloud) ─────────
Source: "{#MyDistDir}\tally_sync\*"; \
  DestDir: "{app}\tally_sync"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; ── Setup wizard exe (collects credentials, writes config.ini, creates tasks) ──
Source: "{#MyDistDir}\TallySyncSetup\*"; \
  DestDir: "{app}\TallySyncSetup"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; ── Supplier Bill Tool exe (PDF invoice -> Tally import, self-contained) ───────
Source: "{#MyDistDir}\SupplierBillTool\*"; \
  DestDir: "{app}\SupplierBillTool"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; ── Config template (placeholder only; real config.ini written by wizard) ──────
Source: "..\config.ini.example"; \
  DestDir: "{app}"; \
  DestName: "config.ini.example"; \
  Flags: ignoreversion

[Icons]
; Start menu shortcuts
Name: "{group}\TallySync - Sync Now";    Filename: "{app}\tally_sync\tally_sync.exe"
Name: "{group}\TallySync - Setup";       Filename: "{app}\TallySyncSetup\TallySyncSetup.exe"
Name: "{group}\Supplier Bill Tool";      Filename: "{app}\SupplierBillTool\SupplierBillTool.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
; Launch setup wizard automatically after installation finishes
Filename: "{app}\TallySyncSetup\TallySyncSetup.exe"; \
  Description: "Run TallySync Setup (enter your Supabase and Groq details)"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove all 3 scheduled tasks on uninstall
Filename: "schtasks"; Parameters: "/delete /tn TallySync_11AM /f"; Flags: runhidden; RunOnceId: "DelTask11AM"
Filename: "schtasks"; Parameters: "/delete /tn TallySync_3PM  /f"; Flags: runhidden; RunOnceId: "DelTask3PM"
Filename: "schtasks"; Parameters: "/delete /tn TallySync_6PM  /f"; Flags: runhidden; RunOnceId: "DelTask6PM"
