### Проект: Телеграмм бот (речь в текст)

Телеграм-бот, преобразующий голосовые сообщения в текст с 
использованием OpenAI API Whisper, работающий на Flask,
чтобы клиент мог воспользоваться ботом, реализована оплата
бота через API Юmoney и Flask SQLAlchemy. Бот упакован в 
docker для удобной работы и развертывания.



### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Kuzahka/voice-text.git
```

```
cd Shum
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```



Запустить проект:

```
flask run
```
