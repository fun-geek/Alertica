# database/firebase.py

import pyrebase
from config import FIREBASE_CONFIG

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()
