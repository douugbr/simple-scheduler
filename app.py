from flask import Flask, render_template, send_file
import qrcode
from random import randint

app = Flask(__name__)

@app.route('/')
def generate():
    additional_char = ''
    for i in range(randint(1, 50)):
        for j in range(randint(1, 3)):
            additional_char += '?'
        for j in range(randint(1, 3)):
            additional_char += '='

    text = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' + additional_char
    qr = img = qrcode.make(text)
    qr.save('qr.png')
    response = send_file('qr.png', mimetype='image/gif')
    return response