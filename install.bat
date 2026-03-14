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
if not exist ".\venv\" (
        cd /d "C:\Python\Virtual_Env"
	virtualenv venv && echo [+] Virtual environment is now created
) else (
	echo [v] Virtual environment 'stocks' exists
)
if not exist ".\venv\Scripts\activate.bat" (
	echo Virtual environment incompleted!
	echo Please remove '.\venv' folder and reinstall
	exit /b
)
echo:
echo Ready to active the virtual environment
pause
call .\venv\Scripts\activate.bat
echo Continue to check necessary packages
pause
cls
cd /d "%~dp0"
if not exist ".\venv\Lib\site-packages\requests\" (
        pip install requests && echo [+] Package 'requests' is now installed
) else (
	echo [v] Package 'requests' already installed
)
if not exist ".\venv\Lib\site-packages\pip_system_certs\" (
        pip install pip_system_certs && echo [+] Package 'pip-system-certs' is now installed
) else (
	echo [v] Package 'pip-system-certs' already installed
)
if not exist ".\venv\Lib\site-packages\lxml\" (
        pip install lxml && echo [+] Package 'lxml' is now installed
) else (
	echo [v] Package 'lxml' already installed
)
if not exist ".\venv\Lib\site-packages\pandas\" (
        pip install pandas && echo [+] Package 'pandas' is now installed
) else (
	echo [v] Package 'pandas' already installed
)
if not exist ".\venv\Lib\site-packages\sv_ttk\" (
        pip install sv-ttk && echo [+] Package 'sv-ttk' is now installed
) else (
	echo [v] Package 'sv-ttk' already installed
)
if not exist ".\venv\Lib\site-packages\mplfinance\" (
        pip install mplfinance && echo [+] Package 'mplfinance' is now installed
) else (
	echo [v] Package 'mplfinance' already installed
)
if not exist ".\venv\Lib\site-packages\mplcursors\" (
        pip install mplcursors && echo [+] Package 'mplcursors' is now installed
) else (
	echo [v] Package 'mplcursors' already installed
)
echo.
echo ------------------ -----------
pip list
echo ------------------ -----------
echo All done!
pause
