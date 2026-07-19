from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import requests
from datetime import datetime

islamic_calendar_bp = Blueprint('islamic_calendar', __name__)

@islamic_calendar_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today():
    today    = datetime.now().strftime('%d-%m-%Y')
    response = requests.get(f'http://api.aladhan.com/v1/gToH/{today}')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not fetch Islamic date.'}), 400
    hijri   = data['data']['hijri']
    gregori = data['data']['gregorian']
    return jsonify({
        'gregorian': {
            'date':    gregori['date'],
            'day':     gregori['weekday']['en'],
            'month':   gregori['month']['en'],
            'year':    gregori['year'],
        },
        'hijri': {
            'date':    hijri['date'],
            'day':     hijri['weekday']['en'],
            'month':   hijri['month']['en'],
            'year':    hijri['year'],
            'designation': hijri['designation']['expanded'],
        }
    }), 200


@islamic_calendar_bp.route('/convert/to-hijri', methods=['GET'])
@jwt_required()
def gregorian_to_hijri():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date is required. Format: DD-MM-YYYY'}), 400
    response = requests.get(f'http://api.aladhan.com/v1/gToH/{date}')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not convert date.'}), 400
    hijri = data['data']['hijri']
    return jsonify({
        'gregorian_input': date,
        'hijri': {
            'date':  hijri['date'],
            'day':   hijri['weekday']['en'],
            'month': hijri['month']['en'],
            'year':  hijri['year'],
        }
    }), 200


@islamic_calendar_bp.route('/convert/to-gregorian', methods=['GET'])
@jwt_required()
def hijri_to_gregorian():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'date is required. Format: DD-MM-YYYY (Hijri)'}), 400
    response = requests.get(f'http://api.aladhan.com/v1/hToG/{date}')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not convert date.'}), 400
    gregori = data['data']['gregorian']
    return jsonify({
        'hijri_input': date,
        'gregorian': {
            'date':  gregori['date'],
            'day':   gregori['weekday']['en'],
            'month': gregori['month']['en'],
            'year':  gregori['year'],
        }
    }), 200


@islamic_calendar_bp.route('/islamic-events', methods=['GET'])
@jwt_required()
def get_islamic_events():
    return jsonify({
        'events': [
            {'month': 1,  'name': 'Muharram',       'event': 'Islamic New Year — 1st Muharram'},
            {'month': 1,  'name': 'Ashura',          'event': 'Day of Ashura — 10th Muharram'},
            {'month': 3,  'name': 'Mawlid',          'event': 'Birth of Prophet Muhammad ﷺ — 12th Rabi al-Awwal'},
            {'month': 7,  'name': 'Rajab',           'event': 'Isra and Miraj — 27th Rajab'},
            {'month': 8,  'name': 'Shaban',          'event': 'Shab e Barat — 15th Shaban'},
            {'month': 9,  'name': 'Ramadan',         'event': 'Month of Fasting — entire month'},
            {'month': 9,  'name': 'Laylatul Qadr',   'event': 'Night of Power — last 10 nights of Ramadan'},
            {'month': 10, 'name': 'Eid ul Fitr',     'event': 'Festival of Breaking Fast — 1st Shawwal'},
            {'month': 12, 'name': 'Eid ul Adha',     'event': 'Festival of Sacrifice — 10th Dhul Hijjah'},
            {'month': 12, 'name': 'Hajj',            'event': 'Annual Pilgrimage — 8th to 13th Dhul Hijjah'},
        ]
    }), 200