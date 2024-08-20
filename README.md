# Инструкция по установке и запуску проекта TID (Tweet Input Data)

## 1. Установка Docker и Docker Compose на Ubuntu

1. Обновите систему и установите необходимые пакеты:

    ```bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y ca-certificates curl gnupg lsb-release
    ```

2. Добавьте ключ GPG для репозиториев Docker:

    ```bash
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    ```

3. Добавьте репозиторий Docker в список источников APT:

    ```bash
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

4. Установите Docker и Docker Compose:

    ```bash
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    ```

5. Добавьте пользователя в группу `docker` и установите `docker-compose`:

    ```bash
    sudo groupadd docker
    sudo usermod -aG docker $USER
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```

## 2. Настройка и запуск проекта TID

1. Откройте терминал в папке проекта и сделайте скрипты исполняемыми:

    ```bash
    chmod +x tid.sh
    chmod +x tid.desktop
    ```

2. Переместите `tid.desktop` в директорию приложений:

    ```bash
    mv tid.desktop ~/.local/share/applications/
    ```

## 3. Запуск Docker Compose

1. Создайте и запустите контейнеры с помощью Docker Compose:

    ```bash
    docker-compose up --build
    ```

Теперь проект TID должен быть готов к использованию. Вы можете запустить его с помощью созданного ярлыка на рабочем столе или из терминала.

