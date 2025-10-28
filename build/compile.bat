
rmdir /s /q "%rootdir%\bin\win" >NUL 2>&1
rmdir /s /q "%rootdir%\obj" >NUL 2>&1


pushd "%rootdir%\prj"
make rp
make fcc
popd

@REM copy "%rootdir%\build\7z\7za" ".\bin"