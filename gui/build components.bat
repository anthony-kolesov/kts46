@echo off

pushd .\components

SET ARGS=-m typelib -w -I d:\programs\xulrunner_sdk\idl\
SET XPIDL=d:\programs\xulrunner_sdk\bin\xpidl.exe

%XPIDL% %ARGS% .\nsIRoadNetworkModel.idl
%XPIDL% %ARGS% .\nsISimple.idl
%XPIDL% %ARGS% .\nsIRNModelParams.idl
%XPIDL% %ARGS% .\nsIProgressReportCallback.idl

REM Return console to initial directory.
popd
