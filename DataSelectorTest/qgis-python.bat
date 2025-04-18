@echo off
set OSGEO4W_ROOT=C:\Program Files\QGIS 3.40.5
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"
set PATH=%OSGEO4W_ROOT%\apps\qgis\bin;%PATH%
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis\python;%OSGEO4W_ROOT%\apps\Python312;%OSGEO4W_ROOT%\apps\Python312\Scripts
"%OSGEO4W_ROOT%\bin\python3.exe" %*
