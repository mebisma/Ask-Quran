from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import TasbihCounter

tasbih_bp = Blueprint('tasbih', __name__)

@tasbih_bp.route('/get', methods=['GET'])
@jwt_required()
def get_count():
    user_id = get_jwt_identity()
    tasbih  = TasbihCounter.query.filter_by(user_id=int(user_id)).first()
    if not tasbih:
        tasbih = TasbihCounter(user_id=int(user_id), count=0)
        db.session.add(tasbih)
        db.session.commit()
    return jsonify({'tasbih': tasbih.to_dict()}), 200

@tasbih_bp.route('/increment', methods=['POST'])
@jwt_required()
def increment():
    user_id = get_jwt_identity()
    tasbih  = TasbihCounter.query.filter_by(user_id=int(user_id)).first()
    if not tasbih:
        tasbih = TasbihCounter(user_id=int(user_id), count=0)
        db.session.add(tasbih)
    tasbih.count += 1
    db.session.commit()
    return jsonify({'tasbih': tasbih.to_dict()}), 200

@tasbih_bp.route('/reset', methods=['POST'])
@jwt_required()
def reset():
    user_id = get_jwt_identity()
    tasbih  = TasbihCounter.query.filter_by(user_id=int(user_id)).first()
    if not tasbih:
        tasbih = TasbihCounter(user_id=int(user_id), count=0)
        db.session.add(tasbih)
    tasbih.count = 0
    db.session.commit()
    return jsonify({'message': 'Counter reset.', 'tasbih': tasbih.to_dict()}), 200

@tasbih_bp.route('/set', methods=['POST'])
@jwt_required()
def set_count():
    from flask import request
    user_id = get_jwt_identity()
    data    = request.get_json()
    count   = data.get('count')
    if count is None or int(count) < 0:
        return jsonify({'error': 'Valid count is required.'}), 400
    tasbih = TasbihCounter.query.filter_by(user_id=int(user_id)).first()
    if not tasbih:
        tasbih = TasbihCounter(user_id=int(user_id), count=0)
        db.session.add(tasbih)
    tasbih.count = int(count)
    db.session.commit()
    return jsonify({'message': 'Count saved.', 'tasbih': tasbih.to_dict()}), 200