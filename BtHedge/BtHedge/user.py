"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request
from BtHedge import app
from BtHedge import db
from json import dumps
from BtHedge import btccontroller
from ccxt import bitmex
import bcrypt

def err_400():
    return '', 400

@app.route('/login', methods=['POST'])
def login():
    json = request.get_json()
    if not json:
        return err_400()

    name_email = json.get('name_email')
    password = json.get('password')

    if not (name_email and password):
        return err_400()

    cursor = db.cursor()
    field = ""
    if "@" in name_email:
        field = "email"
    else:
        field = "username"
    
    cursor.execute("SELECT u.id, u.username, u.email, u.password, u.address, u.personal_balance  FROM user u LEFT JOIN transaction t on t.user = u.id WHERE u."+field+" = %s", (name_email,))

    user = cursor.fetchone()

    print(bcrypt.hashpw(password.encode('utf8'), user[3].encode('utf8')))
    if not bcrypt.hashpw(password.encode('utf8'), user[3].encode('utf8')) == user[3].encode('utf8'):
        return '', 401

    balance = btccontroller.get_balance(user[4])

    #if balance:
    """
        In this case we want to place an order with these funds on BitMEX
    """
    cursor.execute("UPDATE user u SET u.personal_balance = u.personal_balance + %d", (balance,))

    user += (balance,)

    return dumps(user)

@app.route('/register', methods=['POST'])
def register():
    json = request.get_json()
    if not json:
        return err_400()

    username = json.get('username')
    email = json.get('email')
    password = json.get('password')
    
    if not (username and email and password):
        return err_400()

    hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

    cursor = db.cursor()
    cursor.execute("SELECT address FROM addresses limit 1")
    address = cursor.fetchone()

    cursor.execute("DELETE FROM addresses WHERE address = %s", (address,))

    cursor.execute("INSERT INTO user (username, email, password, address) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, address))

    db.commit()

    return ''

@app.route('/record/add', methods=['POST'])
def add_record():
    json = request.json
    if not json:
        return err_400()

    user_id = int(json.get('user_id'))
    transaction_type = json.get('type').upper()
    usd = int(json.get('usd'))
    btc = int(json.get('btc'))
    difference = int(json.get('diff'))

    if not (user_id and usd and btc and difference and (transaction_type=="BUY" or transaction_type=="SELL")):
        return err_400

    cursor = db.cursor()
    cursor.execute("INSERT INTO transaction (user, type, usd_amount, btc_amount, market_diff) VALUES (%s, %s, %s, %s, %s)", (user_id, transaction_type, usd, btc, difference))
    
    cursor.execute("SELECT * FROM user u WHERE id = %d", (user_id,))
    user = cursor.fetchone()

    # invest that balance on bitmex
    client = bitmex({
        "test": True,
        "apiKey": user[6],
        "secret":user[7]
    })

    if transaction_type == "BUY":
        client.create_order("BTC", "Market", "SELL", total_balance)
    else:
        client.create_order("BTC", "Market", "BUY", total_balance)

    db.commit()
    return ''