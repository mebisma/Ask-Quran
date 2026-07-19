from flask import Flask
from extensions import db, bcrypt, jwt
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from jwt_callbacks import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    from routes.auth             import auth_bp
    from routes.quran            import quran_bp
    from routes.tasbih           import tasbih_bp
    from routes.prayer           import prayer_bp
    from routes.zakat            import zakat_bp
    from routes.ask_quran        import ask_quran_bp
    from routes.islamic_calendar import islamic_calendar_bp
    from routes.names            import names_bp
    from routes.duas             import duas_bp
    from routes.settings         import settings_bp
    from routes.reminders        import reminders_bp
    from routes.offline_sync     import offline_sync_bp
    from routes.voice_search     import voice_search_bp
    from routes.assessment       import assessment_bp
    from routes.lessons import lessons_bp
    from routes.gamification import gamification_bp
    
    app.register_blueprint(auth_bp,             url_prefix='/api/auth')
    app.register_blueprint(quran_bp,            url_prefix='/api/quran')
    app.register_blueprint(tasbih_bp,           url_prefix='/api/tasbih')
    app.register_blueprint(prayer_bp,           url_prefix='/api/prayer')
    app.register_blueprint(zakat_bp,            url_prefix='/api/zakat')
    app.register_blueprint(ask_quran_bp,        url_prefix='/api/askquran')
    app.register_blueprint(islamic_calendar_bp, url_prefix='/api/calendar')
    app.register_blueprint(names_bp,            url_prefix='/api/names')
    app.register_blueprint(duas_bp,             url_prefix='/api/duas')
    app.register_blueprint(settings_bp,         url_prefix='/api/settings')
    app.register_blueprint(reminders_bp,        url_prefix='/api/reminders')
    app.register_blueprint(offline_sync_bp,     url_prefix='/api/sync')
    app.register_blueprint(voice_search_bp,     url_prefix='/api/voice')
    app.register_blueprint(assessment_bp,       url_prefix='/api/assessment')
    app.register_blueprint(lessons_bp, url_prefix='/api/lessons')
    app.register_blueprint(gamification_bp, url_prefix='/api/gamification')


    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)