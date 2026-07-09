from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app(config_object="app.config.DevConfig"):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_object)

    db.init_app(app)
    CORS(app)  # fine for local/portfolio use; lock down origins before any real deployment

    from app.routes.cards import cards_bp
    from app.routes.activity import activity_bp

    app.register_blueprint(cards_bp)
    app.register_blueprint(activity_bp)

    from flask import render_template

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
