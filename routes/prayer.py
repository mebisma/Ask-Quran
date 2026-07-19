from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import UserLocation
import requests
from datetime import datetime

prayer_bp = Blueprint('prayer', __name__)

@prayer_bp.route('/times', methods=['GET'])
@jwt_required()
def get_prayer_times():
    user_id = get_jwt_identity()
    location = UserLocation.query.filter_by(user_id=int(user_id)).first()

    if not location:
        return jsonify({'error': 'Location not set. Please set your city first.'}), 404

    today = datetime.now().strftime('%d-%m-%Y')
    url   = f'http://api.aladhan.com/v1/timingsByCity/{today}'
    params = {
        'city':    location.city,
        'country': location.country,
        'method':  2
    }

    response = requests.get(url, params=params)
    data     = response.json()

    if data['code'] != 200:
        return jsonify({'error': 'Could not fetch prayer times.'}), 400

    timings = data['data']['timings']

    prayer_times = {
        'Fajr':    timings['Fajr'],
        'Dhuhr':   timings['Dhuhr'],
        'Asr':     timings['Asr'],
        'Maghrib': timings['Maghrib'],
        'Isha':    timings['Isha'],
        'date':    today,
        'city':    location.city,
        'country': location.country,
    }

    next_prayer = get_next_prayer(prayer_times)
    prayer_times['next_prayer'] = next_prayer

    return jsonify({'prayer_times': prayer_times}), 200


@prayer_bp.route('/location', methods=['POST'])
@jwt_required()
def set_location():
    user_id = get_jwt_identity()
    data    = request.get_json()
    city    = data.get('city')
    country = data.get('country')

    if not city or not country:
        return jsonify({'error': 'City and country are required.'}), 400

    location = UserLocation.query.filter_by(user_id=int(user_id)).first()
    if not location:
        location = UserLocation(user_id=int(user_id))
        db.session.add(location)

    location.city    = city
    location.country = country
    db.session.commit()

    return jsonify({'message': 'Location saved.', 'location': location.to_dict()}), 200


@prayer_bp.route('/location', methods=['GET'])
@jwt_required()
def get_location():
    user_id  = get_jwt_identity()
    location = UserLocation.query.filter_by(user_id=int(user_id)).first()

    if not location:
        return jsonify({'error': 'Location not set.'}), 404

    return jsonify({'location': location.to_dict()}), 200


def get_next_prayer(prayer_times):
    prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
    now     = datetime.now().strftime('%H:%M')

    for prayer in prayers:
        if prayer_times[prayer] > now:
            return {
                'name': prayer,
                'time': prayer_times[prayer]
            }

    return {
        'name': 'Fajr',
        'time': prayer_times['Fajr'],
        'note': 'Tomorrow'
    }