@Echo off
if not exist "C:\Python\Virtual_Env\stocks\" (
	echo Virtual environment 'stocks' not created
	pause
	exit /b
)
if not exist "C:\Python\Virtual_Env\stocks\Scripts\activate.bat" (
	echo Virtual environment 'stocks' not setup correctly
	pause
	exit /b
)
call C:\Python\Virtual_Env\stocks\Scripts\activate.bat
python src\db_manager.py download
pause