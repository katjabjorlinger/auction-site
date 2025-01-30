
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, jsonify, request, Blueprint, request, jsonify, redirect, url_for, flash, make_response, session
import json

#importerar blueprint för auctions från mybluprints
from myblueprints.auction_bp.auction_bp import auction_bp, login_manager, mail


app = Flask(__name__)

#secret key for login manager
app.config['SECRET_KEY'] = 'hard_to&guess%str1ngsdf8646523q45kabufg'

login_manager.init_app(app)

#sätter upp server och det konto som mejl ska skickas ifr¨ån med flask mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Exempelserver
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'noreply.auktionstorget@gmail.com'
app.config['MAIL_PASSWORD'] = 'ulgq cxtx iepv ethf'

mail.init_app(app)

#registrerar blueprintet hos appen med prefixet auction
app.register_blueprint(auction_bp, url_prefix='/auction')


@app.route('/')
def hello_world():
    return 'Hello from Flask!'


