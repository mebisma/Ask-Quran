from flask import jsonify
from flask_jwt_extended import JWTManager
from models import TokenBlocklist

def register_jwt_callbacks(jwt: JWTManager):

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has been revoked. Please log in again.'}), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired. Please refresh or log in again.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(error):
        return jsonify({'error': 'Invalid token.'}), 422

    @jwt.unauthorized_loader
    def missing_token_response(error):
        return jsonify({'error': 'Authorization token is missing.'}), 401