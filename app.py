from flask import Flask, request
import requests
from dotenv import load_dotenv
import os
from os.path import join, dirname
from yookassa import Configuration, Payment
import json
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

client = OpenAI()


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String, nullable=False)
    invoice = db.Column(db.Boolean, unique=False, default=False)


def create_invoice(chat_id):
    Configuration.account_id = get_from_env("SHOP_ID")
    Configuration.secret_key = get_from_env("PAYMENT_TOKEN")

    payment = Payment.create({
        "amount": {
            "value": "100.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.google.com"
        },
        "capture": True,
        "description": "Заказ №1",
        "metadata": {"chat_id": chat_id}
    })

    return payment.confirmation.confirmation_url


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)  # возвращен серкетный токен (или ключ к платежной системе)


def send_message(chat_id, text):
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


def send_pay_button(chat_id, text):
    invoice_url = create_invoice(chat_id)

    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": [[{
        "text": "Оплатить!",
        "url": f"{invoice_url}"
    }]]})}

    requests.post(url, data=data)


def check_if_successful_payment(request):
    try:
        if request.json["event"] == "payment.succeeded":
            return True
    except KeyError:
        return False

    return False


def get_voice(request, chat_id):
    new_file = request.json['message']['voice']['file_id']
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    file_path = requests.get(
        f'https://api.telegram.org/bot{token}/getFile?file_id={new_file}')
    file_download = file_path.json()['result']['file_path']
    response = requests.get(
        f'https://api.telegram.org/file/bot{token}/{file_download}')
    with open("voice_note.mp3", mode="wb") as file:
        file.write(response.content)
    audio_file = open("voice_note.mp3", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    send_message(chat_id, transcript)


def say_answer(request, chat_id):
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=request.json['message']['text'],
        max_tokens=300,
        temperature=0.7,
    )
    send_message(chat_id, response.choices[0].text.strip())


@app.route('/', methods=["POST"])  # localhost:5000/ - на этот адрес телеграм шлет свои сообщение
def process():
    if check_if_successful_payment(request):
        # Обработка запроса от Юкассы
        chat_id = request.json["object"]["metadata"]["chat_id"]
        Invoice.query.filter_by(client=chat_id).first().invoice = True
        db.session.commit()
        send_message(chat_id, "Оплата прошла успешно")
    else:
        # Обработка запроса от Телеграм
        chat_id = request.json["message"]["chat"]["id"]
        if Invoice.query.filter_by(client=chat_id).first() is None:
            payer = Invoice(
                client=chat_id,
            )
            db.session.add(payer)
            db.session.commit()
            send_pay_button(chat_id=chat_id, text="Тестовая оплата")
        elif Invoice.query.filter_by(client=chat_id).first().invoice and request.json['message'].get(
                'voice') is not None:
            get_voice(request, chat_id)
        elif Invoice.query.filter_by(client=chat_id).first().invoice and request.json['message'].get(
                'text') is not None:
            say_answer(request, chat_id)
        else:
            send_pay_button(chat_id=chat_id, text="Тестовая оплата")
    return {"ok": True}


if __name__ == '__main__':
    app.run()
