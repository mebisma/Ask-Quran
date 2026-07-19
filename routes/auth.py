from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
)
from extensions import db
from models import User, ReadingProgress, TokenBlocklist
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email))

def validate_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number.'
    return True, ''

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required = ['username', 'email', 'password']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    username = data['username'].strip()
    email    = data['email'].strip().lower()
    password = data['password']

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters.'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email address.'}), 400
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({'error': msg}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken.'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered.'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    progress = ReadingProgress(user_id=user.id)
    db.session.add(progress)
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        'message': 'Account created successfully.',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data       = request.get_json()
    identifier = data.get('identifier', '').strip()
    password   = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'Identifier and password are required.'}), 400

    if '@' in identifier:
        user = User.query.filter_by(email=identifier.lower()).first()
    else:
        user = User.query.filter_by(username=identifier).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials.'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated.'}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        'message': 'Logged in successfully.',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200

@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id      = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user    = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user    = User.query.get(int(user_id))
    data    = request.get_json()

    if 'username' in data:
        new_username = data['username'].strip()
        if len(new_username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters.'}), 400
        if User.query.filter(User.username == new_username, User.id != user.id).first():
            return jsonify({'error': 'Username already taken.'}), 409
        user.username = new_username

    if 'password' in data:
        valid, msg = validate_password(data['password'])
        if not valid:
            return jsonify({'error': msg}), 400
        user.set_password(data['password'])

    db.session.commit()
    return jsonify({'message': 'Profile updated.', 'user': user.to_dict()}), 200

@auth_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity()
    user    = User.query.get(int(user_id))
    jti     = get_jwt()['jti']
    db.session.add(TokenBlocklist(jti=jti))
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Account deleted.'}), 200