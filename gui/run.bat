@echo off

set VENDOR_NAME=Anthony Kolesov
set PROJECT_NAME=PyXUL_AK

rem Clear cache
rd /S /Q "%APPDATA%\%VENDOR_NAME%\%PROJECT_NAME%\"
rd /S /Q "%USERPROFILE%\Local Settings\Application Data\%VENDOR_NAME%\%PROJECT_NAME%\"

start d:\programs\xulrunner\xulrunner.exe application.ini -jsconsole
