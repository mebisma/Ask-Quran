from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Bookmark, ReadingProgress
import requests

quran_bp = Blueprint('quran', __name__)

# ─── Reading Progress ─────────────────────────────────────────────────────────

@quran_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    user_id  = get_jwt_identity()
    progress = ReadingProgress.query.filter_by(user_id=int(user_id)).first()
    if not progress:
        return jsonify({'error': 'Progress not found.'}), 404
    return jsonify({'progress': progress.to_dict()}), 200

@quran_bp.route('/progress', methods=['PUT'])
@jwt_required()
def update_progress():
    user_id  = get_jwt_identity()
    data     = request.get_json()
    progress = ReadingProgress.query.filter_by(user_id=int(user_id)).first()
    surah = data.get('surah')
    ayah  = data.get('ayah')
    if not surah or not ayah:
        return jsonify({'error': 'surah and ayah are required.'}), 400
    if not (1 <= int(surah) <= 114):
        return jsonify({'error': 'Surah must be between 1 and 114.'}), 400
    progress.last_surah = int(surah)
    progress.last_ayah  = int(ayah)
    db.session.commit()
    return jsonify({'message': 'Progress updated.', 'progress': progress.to_dict()}), 200

# ─── Bookmarks ────────────────────────────────────────────────────────────────

@quran_bp.route('/bookmarks', methods=['GET'])
@jwt_required()
def get_bookmarks():
    user_id   = get_jwt_identity()
    bookmarks = Bookmark.query.filter_by(user_id=int(user_id)).order_by(Bookmark.created_at.desc()).all()
    return jsonify({'bookmarks': [b.to_dict() for b in bookmarks]}), 200

@quran_bp.route('/bookmarks', methods=['POST'])
@jwt_required()
def add_bookmark():
    user_id = get_jwt_identity()
    data    = request.get_json()
    surah   = data.get('surah')
    ayah    = data.get('ayah')
    note    = data.get('note', '')
    if not surah or not ayah:
        return jsonify({'error': 'surah and ayah are required.'}), 400
    if not (1 <= int(surah) <= 114):
        return jsonify({'error': 'Surah must be between 1 and 114.'}), 400
    existing = Bookmark.query.filter_by(user_id=int(user_id), surah=int(surah), ayah=int(ayah)).first()
    if existing:
        return jsonify({'error': 'Ayah already bookmarked.', 'bookmark': existing.to_dict()}), 409
    bookmark = Bookmark(user_id=int(user_id), surah=int(surah), ayah=int(ayah), note=note)
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({'message': 'Bookmarked successfully.', 'bookmark': bookmark.to_dict()}), 201

@quran_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@jwt_required()
def delete_bookmark(bookmark_id):
    user_id  = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=int(user_id)).first()
    if not bookmark:
        return jsonify({'error': 'Bookmark not found.'}), 404
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({'message': 'Bookmark removed.'}), 200

# ─── All Surahs List ──────────────────────────────────────────────────────────

@quran_bp.route('/surahs', methods=['GET'])
@jwt_required()
def get_all_surahs():
    response = requests.get('https://api.alquran.cloud/v1/surah')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not fetch surahs.'}), 400
    surahs = [{
        'number':           s['number'],
        'name_arabic':      s['name'],
        'name_english':     s['englishName'],
        'meaning':          s['englishNameTranslation'],
        'total_ayahs':      s['numberOfAyahs'],
        'revelation_type':  s['revelationType'],
    } for s in data['data']]
    return jsonify({'surahs': surahs}), 200

# ─── Get Surah Arabic ─────────────────────────────────────────────────────────

@quran_bp.route('/arabic/<int:surah_number>', methods=['GET'])
@jwt_required()
def get_arabic_surah(surah_number):
    if not (1 <= surah_number <= 114):
        return jsonify({'error': 'Surah number must be between 1 and 114.'}), 400
    response = requests.get(f'https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not fetch Arabic text.'}), 400
    ayahs = [{'number': a['numberInSurah'], 'arabic': a['text']} for a in data['data']['ayahs']]
    return jsonify({
        'surah_number': surah_number,
        'surah_name':   data['data']['name'],
        'english_name': data['data']['englishName'],
        'total_ayahs':  data['data']['numberOfAyahs'],
        'ayahs':        ayahs
    }), 200

# ─── Get Surah English Translation ───────────────────────────────────────────

@quran_bp.route('/english/<int:surah_number>', methods=['GET'])
@jwt_required()
def get_english_surah(surah_number):
    if not (1 <= surah_number <= 114):
        return jsonify({'error': 'Surah number must be between 1 and 114.'}), 400
    response = requests.get(f'https://api.alquran.cloud/v1/surah/{surah_number}/en.sahih')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Could not fetch English translation.'}), 400
    ayahs = [{'number': a['numberInSurah'], 'english': a['text']} for a in data['data']['ayahs']]
    return jsonify({
        'surah_number': surah_number,
        'surah_name':   data['data']['name'],
        'english_name': data['data']['englishName'],
        'meaning':      data['data']['englishNameTranslation'],
        'total_ayahs':  data['data']['numberOfAyahs'],
        'ayahs':        ayahs
    }), 200

# ─── Get Surah Arabic + English Together ─────────────────────────────────────

@quran_bp.route('/surah/<int:surah_number>', methods=['GET'])
@jwt_required()
def get_surah_full(surah_number):
    if not (1 <= surah_number <= 114):
        return jsonify({'error': 'Surah number must be between 1 and 114.'}), 400
    arabic_res  = requests.get(f'https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy')
    english_res = requests.get(f'https://api.alquran.cloud/v1/surah/{surah_number}/en.sahih')
    arabic_data  = arabic_res.json()
    english_data = english_res.json()
    if arabic_data['code'] != 200 or english_data['code'] != 200:
        return jsonify({'error': 'Could not fetch surah.'}), 400
    ayahs = []
    for ar, en in zip(arabic_data['data']['ayahs'], english_data['data']['ayahs']):
        ayahs.append({
            'number':  ar['numberInSurah'],
            'arabic':  ar['text'],
            'english': en['text'],
        })
    return jsonify({
        'surah_number': surah_number,
        'surah_name':   arabic_data['data']['name'],
        'english_name': arabic_data['data']['englishName'],
        'meaning':      arabic_data['data']['englishNameTranslation'],
        'total_ayahs':  arabic_data['data']['numberOfAyahs'],
        'revelation':   arabic_data['data']['revelationType'],
        'ayahs':        ayahs
    }), 200

# ─── Get Single Ayah ─────────────────────────────────────────────────────────

@quran_bp.route('/ayah/<int:surah_number>/<int:ayah_number>', methods=['GET'])
@jwt_required()
def get_ayah(surah_number, ayah_number):
    arabic_res  = requests.get(f'https://api.alquran.cloud/v1/ayah/{surah_number}:{ayah_number}/ar.alafasy')
    english_res = requests.get(f'https://api.alquran.cloud/v1/ayah/{surah_number}:{ayah_number}/en.sahih')
    arabic_data  = arabic_res.json()
    english_data = english_res.json()
    if arabic_data['code'] != 200:
        return jsonify({'error': 'Ayah not found.'}), 404
    return jsonify({
        'surah':   surah_number,
        'ayah':    ayah_number,
        'arabic':  arabic_data['data']['text'],
        'english': english_data['data']['text'],
    }), 200

# ─── Search Quran ─────────────────────────────────────────────────────────────

@quran_bp.route('/search', methods=['GET'])
@jwt_required()
def search_quran():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'error': 'Search keyword is required. Use ?q=keyword'}), 400
    response = requests.get(f'https://api.alquran.cloud/v1/search/{keyword}/all/en.sahih')
    data     = response.json()
    if data['code'] != 200:
        return jsonify({'error': 'Search failed.'}), 400
    results = [{
        'surah_number': m['surah']['number'],
        'surah_name':   m['surah']['englishName'],
        'ayah_number':  m['numberInSurah'],
        'text':         m['text'],
    } for m in data['data']['matches']]
    return jsonify({
        'keyword': keyword,
        'total':   data['data']['count'],
        'results': results
    }), 200

# ─── Get Random Ayah ─────────────────────────────────────────────────────────

@quran_bp.route('/random', methods=['GET'])
@jwt_required()
def get_random_ayah():
    import random
    surah  = random.randint(1, 114)
    response = requests.get(f'https://api.alquran.cloud/v1/surah/{surah}')
    data     = response.json()
    total    = data['data']['numberOfAyahs']
    ayah     = random.randint(1, total)
    arabic_res  = requests.get(f'https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy')
    english_res = requests.get(f'https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.sahih')
    return jsonify({
        'surah':        surah,
        'ayah':         ayah,
        'surah_name':   arabic_res.json()['data']['surah']['englishName'],
        'arabic':       arabic_res.json()['data']['text'],
        'english':      english_res.json()['data']['text'],
    }), 200