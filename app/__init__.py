from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import logging

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Add logging configuration
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bridges.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        from .routes import main
        app.register_blueprint(main)
        db.create_all()

    return app
