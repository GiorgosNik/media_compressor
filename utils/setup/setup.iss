[Setup]
AppName=GEP Media Compressor      
OutputDir=../../dist
AppVersion=1.0.0
OutputBaseFilename=GEP Media Compressor Installer
DefaultDirName={autopf}\GEP Media Compressor    
Compression=lzma
SolidCompression=yes
SetupIconFile=../../assets/ges.ico  

[Files]
Source: "../../dist/GEP Media Compressor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "../../assets/ges.ico"; DestDir: "{app}/assets"; Flags: ignoreversion
Source: "../../ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "../../ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional tasks"; Flags: unchecked

[Icons]
Name: "{group}\GEP Media Compressor"; Filename: "{app}\GEP Media Compressor.exe"
Name: "{autodesktop}\GEP Media Compressor"; Filename: "{app}\GEP Media Compressor.exe"; IconFilename: "{app}/assets/ges.ico"; Tasks: desktopicon