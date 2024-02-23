# To start up, enter:
# .\startScript.ps1

Write-Host "Starting Python Environment"

# Activate virtual environment
.\virt\Scripts\Activate.ps1

Start-Sleep -Seconds 2

Write-Host "Set ENV Variables"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:FLASK_APP = "sakila_db.py"
Write-Host "ENV Variables Set"

Write-Host "Starting Flask Server"
python -m flask run
