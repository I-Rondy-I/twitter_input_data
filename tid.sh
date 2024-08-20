#!/bin/bash
echo "Starting Docker Compose Build and Up..."

# Otwórz nowy terminal i uruchom docker-compose up --build
gnome-terminal -- bash -c "cd /home/rondy/Desktop/tweet_input && docker-compose up --build; exec bash"

