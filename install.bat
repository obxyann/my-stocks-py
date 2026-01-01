@echo off
for %%X in (python3.dll) do (set FOUND=%%~$PATH:X)
if not defined FOUND (
	echo Python3 not installed or not found in PATH environment
	exit /b
) else (
	echo [v] Python3 already installed
)
for %%X in (pip3.exe) do (set FOUND=%%~$PATH:X)
if not defined FOUND (
	echo Not found pip3.exe in PATH environment
	exit /b
)
for %%X in (virtualenv.exe) do (set FOUND=%%~$PATH:X)
if not defined FOUND (
	pip install virtualenv && echo [+] Tool 'virtualenv' is now installed
) else (
	echo [v] Tool 'virtualenv' already installed
)
if not exist "C:\Python\" (
	mkdir "C:\Python" && echo [+] Folder 'Python' is now created
) else (
	echo [v] Folder 'C:\Python' exists
)
if not exist "C:\Python\Virtual_Env\" (
	mkdir "C:\Python\Virtual_Env" && echo [+] Folder 'Virtual_Env' is now created
) else (
	echo [v] Folder 'C:\Python\Virtual_Env' exists
)
if not exist "C:\Python\Virtual_Env\stocks\" (
        cd /d "C:\Python\Virtual_Env"
	virtualenv stocks && echo [+] Virtual environment 'stocks' is now created
) else (
	echo [v] Virtual environment 'stocks' exists
)
if not exist "C:\Python\Virtual_Env\stocks\Scripts\activate.bat" (
	echo Virtual environment 'stocks' incompleted!
	echo Please remove 'C:\Python\Virtual_Env\stocks' folder and reinstall
	exit /b
)
echo:
echo Ready to active the virtual environment
pause
call C:\Python\Virtual_Env\stocks\Scripts\activate.bat
echo Continue to check necessary packages
pause
cls
cd /d "%~dp0"
if not exist "C:\Python\Virtual_Env\stocks\Lib\site-packages\requests\" (
        pip install requests && echo [+] Package 'requests' is now installed
) else (
	echo [v] Package 'requests' already installed
)
if not exist "C:\Python\Virtual_Env\stocks\Lib\site-packages\pip_system_certs\" (
        pip install pip_system_certs && echo [+] Package 'pip-system-certs' is now installed
) else (
	echo [v] Package 'pip-system-certs' already installed
)
if not exist "C:\Python\Virtual_Env\stocks\Lib\site-packages\lxml\" (
        pip install lxml && echo [+] Package 'lxml' is now installed
) else (
	echo [v] Package 'lxml' already installed
)
if not exist "C:\Python\Virtual_Env\stocks\Lib\site-packages\pandas\" (
        pip install pandas && echo [+] Package 'pandas' is now installed
) else (
	echo [v] Package 'pandas' already installed
)
echo.
echo ------------------ -----------
pip list
echo ------------------ -----------
echo All done!
pause
