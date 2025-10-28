:: # Script to compile the modified EddyPro source code
:: # Written by June Skeeter
:: # Under development, adaption of linux procedures, no guarantees this will work yet


@echo off
setlocal

:: Get root directory of the batch script

set "rootdir=%~dp0"
:: Remove trailing backslash if present
if "%rootdir:~-1%"=="\" set "rootdir=%rootdir:~0,-1%"

if "%1"=="build" (
    "%rootdir%\build\compile.bat"
)

@REM :: Run the program
@REM pushd "%rootdir%\eddypro-engine"
@REM "%rootdir%\eddypro-engine\bin\win\eddypro_rp" -s win "%rootdir%\custom\SCL_ecf32_win.eddypro"
@REM popd

endlocal
