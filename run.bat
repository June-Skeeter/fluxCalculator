@REM # Script to compile the modified EddyPro source code
@REM # Written by June Skeeter
@REM # Under development, adaption of linux procedures, no guarantees this will work yet

SET rootdir=%~dp0

cd %rootdir%

rmdir /s /q ..\bin ..\obj
cd ./prj

@REM make rp
@REM cd ../../
@REM .\eddypro-engine\bin\win\eddypro_rp.exe -s win C:\Users\User\EP_API_Test\custom\BinTest_win.eddypro