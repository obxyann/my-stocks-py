@Echo off
if not exist "C:\Python\Virtual_Env\OpenData\" (
	echo Virtual environment 'OpenData' not created
	pause
	exit /b
)
if not exist "C:\Python\Virtual_Env\OpenData\Scripts\activate.bat" (
	echo Virtual environment 'OpenData' not setup correctly
	pause
	exit /b
)
:: if not exist "C:\Python\Virtual_Env\OpenData\Lib\site-packages\XX\" (
:: 	echo Package 'XX' not installed
:: 	pause
:: 	exit /b
:: )

:: cmd /k "call C:\Python\Virtual_Env\OpenData\Scripts\activate.bat && python getOpenData.py"
:: or
:: cmd /k "call C:\Python\Virtual_Env\OpenData\Scripts\activate.bat"
:: or

set CMDER_ROOT=C:\Utils\System\cmder

set MY_COMMAND=call C:\Python\Virtual_Env\OpenData\Scripts\activate.bat
start %CMDER_ROOT%\vendor\conemu-maximus5\ConEmu.exe -icon "%CMDER_ROOT%\cmder.exe" -title Cmder -loadcfgfile "%CMDER_ROOT%\_OB\ConEmu.xml" -run cmd /k "%CMDER_ROOT%\vendor\init.bat cd %CD% && %MY_COMMAND%"
