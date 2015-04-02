@echo off
set PATH=%~dp0..\cygwin\bin;%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\system32\Wbem
set CYGWIN=nodosfilewarning
set HOME=%~dp0
set LANG=C.UTF-8
set TZ=
set DISPLAY=:9.0
set AUTOTRACE=potrace

pushd "%~dp0.."
 if not exist "cygwin\bin\fontforge.exe" ( 7zr.exe x -aoa -ocygwin _image.7z )
 if not exist "cygwin\bin\fontforge.exe" ( echo ERROR fontforge.exe not found. && pause )
 if not exist "cygwin\etc\passwd" ( mkpasswd > "cygwin\etc\passwd" )
 if not exist "cygwin\etc\group"  ( mkgroup  > "cygwin\etc\group"  )
popd

start /B XWin.exe :9 -multiwindow -nomultimonitors -silent-dup-error

xwin-close.exe -wait
pushd "%~dp0."
  fontforge.exe -lang=py -script powerline-fontpatcher.py ..\SourceTTF\Inconsolata-Regular.ttf
  mv.exe -f Inconsolata-Powerline-Regular.ttf ..\SourceTTF\Inconsolata-Powerline-Regular.ttf
  fontforge.exe -lang=py -script myrica-mm_generator.py
popd
xwin-close.exe -close

pause
