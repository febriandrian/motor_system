@echo off
echo ================================
echo Pulling latest changes from GitHub...
git pull

echo ================================
echo Adding all changes...
git add .

set /p msg="Enter commit message: "
git commit -m "%msg%"

echo ================================
echo Pushing changes to GitHub...
git push

echo ================================
echo Done!
pause
