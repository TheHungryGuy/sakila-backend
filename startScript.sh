#!/bin/bash 

echo "Starting Python Enviroment"
source virt/Scripts/activate

sleep 2

echo "Set ENV Variables"
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=sakila_db.py
echo "ENV Variables Set"

echo "Starting Flask Server"
flask run