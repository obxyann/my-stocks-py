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
call .\venv\Scripts\activate.bat
python src\main.py