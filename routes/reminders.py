from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Reminder, VALID_DAYS, DEFAULT_REPEAT_DAYS, TIME_PATTERN

reminders_bp = Blueprint('reminders', __name__)


def _validate_time(value: str):
    if not value or not TIME_PATTERN.match(str(value).strip()):
        return None
    return str(value).strip()


def _validate_repeat_days(value: str):
    if not value or not str(value).strip():
        return None
    parts = [p.strip().lower() for p in str(value).split(',') if p.strip()]
    if not parts or any(p not in VALID_DAYS for p in parts):
        return None
    seen       = set()
    normalized = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            normalized.append(p)
    return ','.join(normalized)


@reminders_bp.route('/', methods=['POST'])
@jwt_required()
def create_reminder():
    user_id = int(get_jwt_identity())
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400

    data  = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400

    time_value = _validate_time(data.get('time', ''))
    if time_value is None:
        return jsonify({'error': 'time is required in HH:MM 24-hour format'}), 400

    repeat_days = _validate_repeat_days(data.get('repeat_days', DEFAULT_REPEAT_DAYS))
    if repeat_days is None:
        return jsonify({'error': 'repeat_days must be comma-separated: mon,tue,wed,thu,fri,sat,sun'}), 400

    is_active = data.get('is_active', True)
    if not isinstance(is_active, bool):
        return jsonify({'error': 'is_active must be a boolean'}), 400

    reminder = Reminder(
        user_id=user_id,
        title=title,
        time=time_value,
        repeat_days=repeat_days,
        is_active=is_active,
    )
    db.session.add(reminder)
    db.session.commit()
    return jsonify({'message': 'Reminder created.', 'reminder': reminder.to_dict()}), 201


@reminders_bp.route('/', methods=['GET'])
@jwt_required()
def list_reminders():
    user_id   = int(get_jwt_identity())
    reminders = (
        Reminder.query
        .filter_by(user_id=user_id)
        .order_by(Reminder.time.asc(), Reminder.created_at.asc())
        .all()
    )
    return jsonify({
        'user_id':   user_id,
        'count':     len(reminders),
        'reminders': [r.to_dict() for r in reminders],
    }), 200


@reminders_bp.route('/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_reminder(reminder_id: int):
    user_id  = int(get_jwt_identity())
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({'error': f'Reminder {reminder_id} not found'}), 404

    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400

    data = request.get_json(silent=True) or {}

    if 'title' in data:
        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'error': 'title cannot be empty'}), 400
        reminder.title = title

    if 'time' in data:
        time_value = _validate_time(data.get('time', ''))
        if time_value is None:
            return jsonify({'error': 'time must be in HH:MM 24-hour format'}), 400
        reminder.time = time_value

    if 'repeat_days' in data:
        repeat_days = _validate_repeat_days(data.get('repeat_days', ''))
        if repeat_days is None:
            return jsonify({'error': 'repeat_days must be comma-separated: mon,tue,wed,thu,fri,sat,sun'}), 400
        reminder.repeat_days = repeat_days

    if 'is_active' in data:
        is_active = data.get('is_active')
        if not isinstance(is_active, bool):
            return jsonify({'error': 'is_active must be a boolean'}), 400
        reminder.is_active = is_active

    db.session.commit()
    return jsonify({'message': 'Reminder updated.', 'reminder': reminder.to_dict()}), 200


@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id: int):
    user_id  = int(get_jwt_identity())
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()
    if not reminder:
        return jsonify({'error': f'Reminder {reminder_id} not found'}), 404
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({'message': 'Reminder deleted.', 'id': reminder_id}), 200


@reminders_bp.route('/due', methods=['GET'])
@jwt_required()
def get_due_reminders():
    from datetime import datetime
    user_id   = int(get_jwt_identity())
    now_time  = datetime.now().strftime('%H:%M')
    now_day   = VALID_DAYS[datetime.now().weekday()]
    reminders = Reminder.query.filter_by(user_id=user_id, is_active=True, time=now_time).all()
    due       = [r.to_dict() for r in reminders if r.repeats_on(now_day)]
    return jsonify({'due_reminders': due, 'count': len(due), 'checked_at': now_time}), 200