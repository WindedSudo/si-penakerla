import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from app.config import Config
from app.db import close_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf = CSRFProtect(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'warning'

    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    app.teardown_appcontext(close_db)

    from app.routes.auth import auth_bp
    from app.routes.pencari import pencari_bp
    from app.routes.perusahaan import perusahaan_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(pencari_bp)
    app.register_blueprint(perusahaan_bp)
    app.register_blueprint(admin_bp)

    # Inject unread notification count into all templates
    from flask_login import current_user
    from app.models.notifikasi import Notifikasi
    @app.context_processor
    def inject_notifikasi():
        if current_user.is_authenticated:
            return {'notif_unread': Notifikasi.count_unread(current_user.id)}
        return {'notif_unread': 0}

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401
        
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def too_large_error(error):
        from flask import flash, redirect, request
        flash('Ukuran file terlalu besar. Maksimal 5 MB.', 'danger')
        return redirect(request.referrer or '/'), 302

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app
