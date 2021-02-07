@echo off

rem pyInstaller --onefile update-account.py
rem call py -m pipenv shell
pyInstaller main.spec

pause
