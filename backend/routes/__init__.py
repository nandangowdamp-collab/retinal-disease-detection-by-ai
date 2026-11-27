from routes.auth_routes import auth_bp
from routes.patient_routes import patient_bp
from routes.doctor_routes import doctor_bp
from routes.prediction_routes import prediction_bp
from routes.consultation_routes import consultation_bp
from routes.message_routes import message_bp
from routes.admin_routes import admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(consultation_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(admin_bp)
