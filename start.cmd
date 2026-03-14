@Echo off
if not exist ".\venv\" (
	echo Virtual environment not created
	pause
	exit /b
)
if not exist ".\venv\Scripts\activate.bat" (
	echo Virtual environment not setup correctly
	pause
	exit /b
)
:: if not exist ".\venv\Lib\site-packages\XX\" (
:: 	echo Package 'XX' not installed
:: 	pause
:: 	exit /b
:: )

:: cmd /k "call .\venv\Scripts\activate.bat && python foo.py"
:: or
:: cmd /k "call .\venv\Scripts\activate.bat"
:: or

set CMDER_ROOT=C:\Utils\System\cmder

set MY_COMMAND=call .\venv\Scripts\activate.bat
start %CMDER_ROOT%\vendor\conemu-maximus5\ConEmu.exe -icon "%CMDER_ROOT%\cmder.exe" -title Cmder -loadcfgfile "%CMDER_ROOT%\_OB\ConEmu.xml" -run cmd /k "%CMDER_ROOT%\vendor\init.bat cd %CD% && %MY_COMMAND%"
