@echo off
title Python Dependency Installer
color 0A

echo -----------------------------------------
echo Installing required Python libraries...
echo -----------------------------------------

:: Check if pip exists
python -m ensurepip --default-pip

:: Upgrade pip
python -m pip install --upgrade pip

:: Install dependencies
python -m pip install paramiko

echo -----------------------------------------
echo All dependencies installed successfully!
echo You can now run the Python script.
echo -----------------------------------------
pause
