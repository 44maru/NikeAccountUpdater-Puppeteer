@echo off

call py -m pipenv shell
rem pyInstaller --onefile update-account.py
pyInstaller update-account.spec

pause
