@echo off
setlocal EnableDelayedExpansion
rem Get path from first parameter
set return_path=%1

rem Start pabot
cd /D%return_path%
pabot --argumentfile %3 --listener %5 %6