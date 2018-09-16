# # 项目结构规范:
# |-flasky
#     |-app/
#         |-templates/
#         |-static/
#         |-main/
#             |-__init__.py
#             |-errors.py
#             |-forms.py
#             |-views.py
#         |-__init__.py
#         |-email.py
#         |-models.py
#     |-migrations/
#     |-tests/
#         |-__init__.py
#         |-test * .py
#     |-venv/
#     |-requirements.txt
#     |-config_scrapy.py
#     |-manage.py

import sys
from flask import Flask
#from config import Config
#from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY']="you-will-never-guess"

#app.config.from_object(Config)
#db = SQLAlchemy(app)
from app.views import *
