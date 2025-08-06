@echo off
echo ================================
echo Pulling latest changes from GitHub...
git pull

echo ================================
echo Adding all changes...
git add .

set datetime=%date% %time%
git commit -m "Auto update on %date% %time%"

echo ================================
echo Pushing changes to GitHub...
git push

echo ================================
echo Done!
pause
