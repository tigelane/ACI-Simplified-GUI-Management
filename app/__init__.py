from flask import Flask

app = Flask(__name__)
app.config['TESTING'] = False
app.config['ENV'] = 'production'

from app import routes
