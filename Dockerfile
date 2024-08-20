# Wybór oficjalnego obrazu z Pythonem jako bazowego
FROM python:3.11-slim

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libegl1 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-render0 \
    libxcb-shm0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libqt5dbus5 \
    libqt5core5a \
    libqt5gui5 \
    fonts-noto-color-emoji \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Ustawienie katalogu roboczego w kontenerze
WORKDIR /app

# Skopiowanie pliku requirements.txt do katalogu roboczego
COPY requirements.txt .

# Instalacja zależności
RUN pip install --no-cache-dir -r requirements.txt

# Skopiowanie reszty plików do kontenera
COPY . .

# Komenda do uruchomienia aplikacji PyQt6
CMD ["python", "main.py"]

