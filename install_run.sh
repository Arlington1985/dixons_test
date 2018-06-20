#!/bin/bash

#setting environment script
sudo apt-get install -y docker
docker run -d --hostname localhost --name rabbitmq -p 15672:15672 -p 5672:5672 rabbitmq:3-management
sudo apt-get install -y python3
sudo apt-get install -y python3-pip
sudo pip3 install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python consumer.py
