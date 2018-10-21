"""
The flask application package.
"""

from flask import Flask
import MySQLdb

app = Flask(__name__)

db = MySQLdb.connect(host="localhost", port=3306, user="root", passwd="230593Mayo", db="bthedge")

import BtHedge.user
import BtHedge.btccontroller
