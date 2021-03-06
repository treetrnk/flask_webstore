import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))
datadir = os.path.join(os.path.dirname(basedir), 'data/flask_webstore/')
staticdir = os.path.join(basedir, 'app/static/')
uploaddir = os.path.join(basedir, 'uploads/')
logdir = os.path.join(basedir, 'textlogs/')

class Config(object): 
    env = os.environ.get('FLASK_ENV')
    if env and env == 'development':
        DEBUG = True
        DEVELOPMENT = True
        if os.environ.get('MAIL_SUPPRESS_SEND') == 'False':
            MAIL_SUPPRESS_SEND = False
        else:
            MAIL_SUPPRESS_SEND = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lkdsnfowqieo1293012nindsak012'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(datadir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = os.environ.get('SQLALCHEMY_POOL_RECYCLE') or 3600
    SQLALCHEMY_POOL_TIMEOUT = os.environ.get('SQLALCHEMY_POOL_TIMEOUT') or 60
    SESSION_PERMANENT = True
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=150)
    REMEMBER_COOKIE_DURATION = timedelta(days=150)
    # The maximum number of items the session stores 
    # before it starts deleting some, default 500
    SESSION_FILE_THRESHOLD = os.environ.get('SESSION_FILE_THRESHOLD') or 500
    SESSION_FILE_THRESHOLD = int(SESSION_FILE_THRESHOLD)
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ['MAIL_USERNAME']
    MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    DATA_DIR = datadir
    BASE_DIR = basedir
    UPLOAD_DIR = uploaddir
    LOG_DIR = logdir
    PRODUCT_LOG_DIR = os.path.join(logdir, 'products/')
    BASE_URL = os.environ.get('BASE_URL') or 'localhost:5000'
    ADMINS = os.environ.get('ADMINS') or ''
    ADMINS = ADMINS.split()
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Webstore'
    COMPANY_TAGLINE = os.environ.get('COMPANY_TAGLINE') or COMPANY_NAME
    STRIPE_PUBLISHABLE = os.environ.get('STRIPE_PUBLISHABLE') or ''
    STRIPE_SECRET = os.environ.get('STRIPE_SECRET') or ''
    STRIPE_WEBHOOK = os.environ.get('STRIPE_WEBHOOK') or ''
    LOW_AVAILABILITY_THRESHOLD = os.environ.get('LOW_AVAILABILITY_THRESHOLD') or 3
    LOW_AVAILABILITY_THRESHOLD = int(LOW_AVAILABILITY_THRESHOLD)
