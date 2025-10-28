
rmdir /s /q "%rootdir%\bin" >NUL 2>&1
rmdir /s /q "%rootdir%\obj" >NUL 2>&1


pushd "%rootdir%\prj"
make rp
@REM make fcc
popd

copy "%rootdir%\build\7z\7za" ".\bin"