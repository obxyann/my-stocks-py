@Echo off
if not exist "C:\Python\Virtual_Env\yFinance\" (
	echo Virtual environment 'yFinance' not created
	pause
	exit /b
)
if not exist "C:\Python\Virtual_Env\yFinance\Scripts\activate.bat" (
	echo Virtual environment 'yFinance' not setup correctly
	pause
	exit /b
)
if not exist "C:\Python\Virtual_Env\yFinance\Lib\site-packages\yFinance\" (
	echo Package 'yFinance' not installed
	pause
	exit /b
)

:: cmd /k "call C:\Python\Virtual_Env\yFinance\Scripts\activate.bat && python getYFinance.py"
:: or
:: cmd /k "call C:\Python\Virtual_Env\yFinance\Scripts\activate.bat"
:: or

set CMDER_ROOT=C:\Utils\System\cmder

set MY_COMMAND=call C:\Python\Virtual_Env\yFinance\Scripts\activate.bat
start %CMDER_ROOT%\vendor\conemu-maximus5\ConEmu.exe -icon "%CMDER_ROOT%\cmder.exe" -title Cmder -loadcfgfile "%CMDER_ROOT%\_OB\ConEmu.xml" -run cmd /k "%CMDER_ROOT%\vendor\init.bat cd %CD% && %MY_COMMAND%"
