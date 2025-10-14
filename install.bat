@echo off
for %%X in (python3.dll) do (set FOUND=%%~$PATH:X)
if not defined FOUND (
	echo Python3 not installed or not found in PATH environment
	exit /b
) else (
	echo [v] Python3 installed
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
	echo [v] Tool 'virtualenv' installed
)
C:
if not exist "C:\Python" (
	mkdir "Python" && echo [+] Folder 'Python' is now created
) else (
	echo [v] Folder 'C:\Python' exists
)
cd "C:\Python"
if not exist "Virtual_Env\" (
	mkdir "Virtual_Env" && echo [+] Folder 'Virtual_Env' is now created
) else (
	echo [v] Folder 'C:\Python\Virtual_Env' exists
)
cd "C:\Python\Virtual_Env"
if not exist "yFinance\" (
	virtualenv yFinance && echo [+] Virtual environment 'yFinance' is now created
) else (
	echo [v] Virtual environment 'yFinance' exists
)
if not exist "C:\Python\Virtual_Env\yFinance\Scripts\activate.bat" (
	echo Virtual environment 'yFinance' incompleted!
	echo Please remove 'C:\Python\Virtual_Env\yFinance' folder and reinstall
	exit /b
)
echo:
echo Ready to active the virtual environment
pause 
call C:\Python\Virtual_Env\yFinance\Scripts\activate.bat
if not exist "C:\Python\Virtual_Env\yFinance\Lib\site-packages\yFinance\" (
	pip install yFinance && echo [+] Package 'yFinance' is now installed
) else (
	echo [i] Package 'yFinance' already installed
)
echo ------------------ -----------
pip list
echo ------------------ -----------
echo All done!
pause