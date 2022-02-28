# Сервис для отслеживания автобусов на карте
Сервис получает данные от GPS датчиков, которые установлены в автобусах, и отправляет их клиентскому приложению, например браузеру. Браузер, в свою очередь, отображает движение автобусов на карте. Имитация работы GPS шлюза реализована в скрипте [fake_bus.py](https://github.com/igorzakhar/bus-tracking-py/blob/main/fake_bus.py).

Демонстрация работы сервиса:

![](https://github.com/igorzakhar/bus-tracking-py/blob/main/media/buses.gif)

## Установка

Для запуска сервиса нужен предустановленный Python версии не ниже 3.8+ (на других версиях не проверялся).
Также в программе используются следующие сторонние библиотеки:
- [anyio](https://github.com/agronholm/anyio)
- [asyncclick](https://pypi.org/project/asyncclick/)
- [marshmallow](https://marshmallow.readthedocs.io/en/stable/)
- [trio](https://github.com/python-trio/trio)
- [trio-websocket](https://pypi.org/project/trio-websocket/)


Рекомендуется устанавливать зависимости в виртуальном окружении, используя [virtualenv](https://github.com/pypa/virtualenv) или [venv](https://docs.python.org/3/library/venv.html).

1. Скопируйте репозиторий в текущий каталог. Воспользуйтесь командой:
```bash
$ git clone https://github.com/igorzakhar/bus-tracking-py.git
```
После этого программа будет скопирована в каталог ```bus-tracking-py```

2. Создайте и активируйте виртуальное окружение:
```bash
$ cd bus-tracking-py # Переходим в каталог с программой
$ python3 -m venv my_virtual_environment # Создаем виртуальное окружение
$ source my_virtual_environment/bin/activate # Активируем виртуальное окружение
```

3. Установите сторонние библиотеки  из файла зависимостей:
```bash
$ pip install -r requirements.txt # В качестве альтернативы используйте pip3
```
## Запуск
Запуск основного сервиса:
```bash
$ python3 server.py
```
Серевер запустится по адресу 127.0.0.1 и будет слушать следующие порты:
- ```:8080``` для получения данных от GPS шлюза;
- ```:8000``` для отправки данных клиентскому приложению (например, браузеру).

Запуск имитатора GPS шлюза, который "принимает" данные от GPS трекеров и отправляет нашему сервису:
```bash
$ python3 fake_bus.py
```
По умолчанию имитатор будет отправлять данные о 10 маршрутах, на каждом маршруте "работает" по 10 автобусов (всего 100 автобусов). Данные параметры можно изменить через аргументы командной строки: ```-r``` - количество маршрутов, ```-b``` - количество автобусов на маршруте.
Полный список параметров:
```bash
$ python server.py --help
Usage: server.py [OPTIONS]

Options:
  -h, --host TEXT              Address of the main server.
  -bs, --bus_server TEXT       Address of the tracking server.
  -bp, --browser_port INTEGER  Browser port
  -fp, --bus_port INTEGER      Port of the tracking server.
  -v, --verbose                Enabling verbose logging.
  --help                       Show this message and exit.
```

После запуска ```server.py``` и ```fake_bus.py``` откройте в браузере файл ```frontend/index.html```.

# Цели проекта

Код написан в учебных целях в рамках курса [Devman](https://dvmn.org/modules).