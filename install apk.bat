@echo off
title install %~1 
echo start installing application....
adb install "%~1"
echo finished
REM pause