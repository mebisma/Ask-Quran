from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import UserSettings, VALID_THEMES, VALID_LANGUAGES, MIN_FONT_SIZE, MAX_FONT_SIZE

settings_bp = Blueprint('settings', __name__)


def _get_or_create_settings(user_id: int) -> UserSettings:
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if settings is None:
        settings = UserSettings.create_defaults(user_id)
        db.session.add(settings)
        db.session.commit()
    return settings


@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    user_id  = int(get_jwt_identity())
    settings = _get_or_create_settings(user_id)
    return jsonify({'settings': settings.to_dict()}), 200


@settings_bp.route('/', methods=['PUT'])
@jwt_required()
def update_settings():
    user_id = int(get_jwt_identity())
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400

    data     = request.get_json(silent=True) or {}
    settings = _get_or_create_settings(user_id)

    if 'theme' in data:
        theme = str(data['theme']).strip().lower()
        if theme not in VALID_THEMES:
            return jsonify({'error': f'theme must be one of: {", ".join(VALID_THEMES)}'}), 400
        settings.theme = theme

    if 'font_size' in data:
        try:
            font_size = int(data['font_size'])
        except (TypeError, ValueError):
            return jsonify({'error': 'font_size must be an integer'}), 400
        if not MIN_FONT_SIZE <= font_size <= MAX_FONT_SIZE:
            return jsonify({'error': f'font_size must be between {MIN_FONT_SIZE} and {MAX_FONT_SIZE}'}), 400
        settings.font_size = font_size

    if 'language' in data:
        language = str(data['language']).strip().lower()
        if language not in VALID_LANGUAGES:
            return jsonify({'error': f'language must be one of: {", ".join(VALID_LANGUAGES)}'}), 400
        settings.language = language

    db.session.commit()
    return jsonify({'message': 'Settings updated.', 'settings': settings.to_dict()}), 200