import hashlib
import json
import logging
import os

from random import randint

import mpu
import mysql.connector
import requests

from colorama import Fore, Style
from flask import Flask, request, render_template
from flask_cors import CORS
from waitress import serve

app = Flask(__name__)
CORS(app)


# Logger custom formatter

class CustomFormatter(logging.Formatter):
    green = Fore.GREEN
    yellow = Fore.YELLOW
    red = Fore.RED
    bold_red = Style.BRIGHT + Fore.RED
    reset = Fore.RESET
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Initialise logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialise console logger

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_handler.setFormatter(CustomFormatter())
logger.addHandler(c_handler)

# Initialise file logger

f_handler = logging.FileHandler('routing.log')
f_handler.setLevel(logging.DEBUG)
f_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"))
logger.addHandler(f_handler)


@app.after_request
def Log(response):   
    info = str(request.environ.get('HTTP_X_FORWARDED_FOR', '')) + "==" + str(request.endpoint) + "==" + str(response.status)
    logging.info(info)
    return response


@app.route('/Login')
def Login():
    return render_template('AdminLogin.html')


@app.route('/AddDonations')
def AddDonations():
    return render_template('AddDonation.html')


if __name__ == "__main__":
    # app.run(host="0.0.0.0",port=5001)
    serve(app, host='0.0.0.0', port=5001)
    # serve(app, host='127.0.0.1', port=5001)
    # app.run(debug=True)
