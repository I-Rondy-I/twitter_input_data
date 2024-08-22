#!/bin/bash
echo "Starting Docker Compose Build and Up..."

# Otwórz nowy terminal i uruchom docker-compose up --build
gnome-terminal -- bash -c "cd /home/rondy/Desktop/twitter_input_data && docker-compose up --build; exec bash"

