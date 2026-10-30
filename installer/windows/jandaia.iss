; Instalador do JandAIa para Windows (Inno Setup 6).
; Uso (na raiz do projeto, depois do PyInstaller):
;   ISCC.exe /DMyAppVersion=1.0.0 installer\windows\jandaia.iss
; Saída: dist_installer\JandAIa-Setup-<versão>.exe

#define MyAppName "JandAIa"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "Statlab - Produtos Educacionais"
#define MyAppURL "https://github.com/ProdutosEduacionaisStatlab/JandAIa"
#define MyAppExe "JandAIa.exe"
#define Raiz "..\.."

[Setup]
; ATENCAO: o AppId identifica o programa nas atualizacoes. NUNCA mude depois da primeira versao publicada.
AppId={{EDA66EF9-8440-4D20-9ACF-8C79C0B6E070}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Instala so para o usuario atual (nao pede senha de administrador). Quem quiser pode escolher "todos os usuarios".
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#Raiz}\dist_installer
OutputBaseFilename=JandAIa-Setup-{#MyAppVersion}
SetupIconFile={#Raiz}\assets\jandaia.ico
UninstallDisplayIcon={app}\{#MyAppExe}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
#if FileExists(SourcePath + "\..\..\LICENSE")
LicenseFile={#Raiz}\LICENSE
#endif

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Raiz}\dist\JandAIa\*"; DestDir: "{app}"; Excludes: "*.sqlite3,.env,ssh.key"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autoprograms}\{#MyAppName} - Configurar chave da Groq"; Filename: "{app}\{#MyAppExe}"; Parameters: "--configurar"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Ao desinstalar, pergunta se os dados do usuario (banco e configuracoes) tambem devem ser apagados.
// Por padrao eles sao mantidos, para nao perder questoes cadastradas ao reinstalar/atualizar.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if not UninstallSilent then
    begin
      if MsgBox('Deseja remover também os seus dados do {#MyAppName} (banco de questões e configurações)?' + #13#10 + #13#10 +
                'Escolha "Não" para mantê-los caso reinstale o programa depois.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(ExpandConstant('{localappdata}\{#MyAppName}'), True, True, True);
    end;
  end;
end;
