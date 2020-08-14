import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask
from flask.logging import default_handler
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_session import Session

db = SQLAlchemy()
moment = Moment()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
mail = Mail()
session = Session()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # initialize the DB in app context
    #   http://flask-sqlalchemy.pocoo.org/2.3/contexts/
    db.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    session.init_app(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            """
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], int(app.config['MAIL_PORT'])),
                fromaddr=f"Website Error <{app.config['MAIL_DEFAULT_SENDER']}>",
                toaddrs=app.config['ADMINS'], 
                subject='Website Failure',
                credentials=auth, 
                secure=secure,
            )
            mail_handler.setLevel(logging.DEBUG)
            #logging.getLogger('werkzeug').addHandler(mail_handler)
            app.logger.addHandler(mail_handler)
            """

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(app.config['LOG_DIR'] + f'flask_webstore.log',
                maxBytes=1024000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s|%(levelname)s'
                '|%(pathname)s:%(lineno)d|%(message)s'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            warning_file_handler = RotatingFileHandler(app.config['LOG_DIR'] + f'flask_webstore_warnings.log',
                maxBytes=102400, backupCount=5)
            warning_file_handler.setFormatter(logging.Formatter(
                '%(asctime)s|%(levelname)s'
                '|%(pathname)s:%(lineno)d|%(message)s'))
            warning_file_handler.setLevel(logging.WARNING)
            app.logger.addHandler(warning_file_handler)

        app.logger.setLevel(logging.INFO)
    else:
        app.logger.removeHandler(default_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s|%(levelname)s'
            '|%(filename)s:%(lineno)d|%(message)s'))
        app.logger.addHandler(stream_handler)

    app.logger.info('Webstore Startup')

    return app
