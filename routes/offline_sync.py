import math
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import Ayah, Surah, Hadith, HadithCollection, ContentMetadata

offline_sync_bp = Blueprint('offline_sync', __name__)


def _parse_pagination(default_per_page: int = 100):
    try:
        page     = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', default_per_page))
    except (TypeError, ValueError):
        return None, None
    if page < 1 or per_page < 1:
        return None, None
    return page, min(per_page, 500)


def _pagination_meta(page: int, per_page: int, total_items: int) -> dict:
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
    return {
        'page':        page,
        'per_page':    per_page,
        'total_items': total_items,
        'total_pages': total_pages,
    }


def _group_ayahs_by_surah(ayahs: list) -> list:
    grouped = {}
    order   = []
    for ayah in ayahs:
        if ayah.surah_id not in grouped:
            grouped[ayah.surah_id] = {'surah': ayah.surah.to_dict(), 'ayahs': []}
            order.append(ayah.surah_id)
        grouped[ayah.surah_id]['ayahs'].append(ayah.to_dict())
    return [grouped[sid] for sid in order]


def _group_hadiths_by_collection(hadiths: list) -> list:
    grouped = {}
    order   = []
    for hadith in hadiths:
        if hadith.collection_id not in grouped:
            grouped[hadith.collection_id] = {'collection': hadith.collection.to_dict(), 'hadiths': []}
            order.append(hadith.collection_id)
        grouped[hadith.collection_id]['hadiths'].append(hadith.to_dict())
    return [grouped[cid] for cid in order]


@offline_sync_bp.route('/quran', methods=['GET'])
@jwt_required()
def sync_quran():
    page, per_page = _parse_pagination()
    if page is None:
        return jsonify({'error': 'page and per_page must be positive integers'}), 400

    base_query  = Ayah.query.join(Surah).order_by(Surah.id, Ayah.ayah_number)
    total_items = base_query.count()
    ayahs       = base_query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'pagination': _pagination_meta(page, per_page, total_items),
        'data':       _group_ayahs_by_surah(ayahs),
    }), 200


@offline_sync_bp.route('/hadith', methods=['GET'])
@jwt_required()
def sync_hadith():
    page, per_page = _parse_pagination()
    if page is None:
        return jsonify({'error': 'page and per_page must be positive integers'}), 400

    base_query  = Hadith.query.order_by(Hadith.collection_id, Hadith.id)
    total_items = base_query.count()
    hadiths     = base_query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'pagination': _pagination_meta(page, per_page, total_items),
        'data':       _group_hadiths_by_collection(hadiths),
    }), 200


@offline_sync_bp.route('/version', methods=['GET'])
@jwt_required()
def sync_version():
    metadata = db.session.get(ContentMetadata, 1)
    if metadata is None:
        return jsonify({'error': 'No content metadata found. POST /api/sync/seed first.'}), 404
    return jsonify(metadata.to_dict()), 200


@offline_sync_bp.route('/seed', methods=['POST'])
@jwt_required()
def seed_data():
    force = request.args.get('force', 'false').lower() == 'true'

    if Surah.query.count() > 0 and not force:
        return jsonify({'skipped': True, 'message': 'Content already exists. Use ?force=true to re-seed.'}), 200

    if force:
        Hadith.query.delete()
        HadithCollection.query.delete()
        Ayah.query.delete()
        Surah.query.delete()
        ContentMetadata.query.delete()

    now = datetime.now(timezone.utc)

    SURAH_SEED = [
        {
            "id": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatiha",
            "name_translation": "The Opening", "ayah_count": 7, "revelation_type": "meccan",
            "ayahs": [
                {"ayah_number": 1, "text_arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "text_transliteration": "Bismillahir Rahmanir Raheem", "text_translation": "In the name of Allah, the Entirely Merciful, the Especially Merciful.", "juz": 1, "page": 1},
                {"ayah_number": 2, "text_arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "text_transliteration": "Alhamdu lillahi rabbil alamin", "text_translation": "All praise is due to Allah, Lord of the worlds.", "juz": 1, "page": 1},
                {"ayah_number": 3, "text_arabic": "الرَّحْمَٰنِ الرَّحِيمِ", "text_transliteration": "Ar-Rahmanir-Raheem", "text_translation": "The Entirely Merciful, the Especially Merciful.", "juz": 1, "page": 1},
                {"ayah_number": 4, "text_arabic": "مَالِكِ يَوْمِ الدِّينِ", "text_transliteration": "Maliki yawmid deen", "text_translation": "Sovereign of the Day of Recompense.", "juz": 1, "page": 1},
                {"ayah_number": 5, "text_arabic": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "text_transliteration": "Iyyaka nabudu wa iyyaka nastaeen", "text_translation": "It is You we worship and You we ask for help.", "juz": 1, "page": 1},
                {"ayah_number": 6, "text_arabic": "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", "text_transliteration": "Ihdinas siratal mustaqeem", "text_translation": "Guide us to the straight path.", "juz": 1, "page": 1},
                {"ayah_number": 7, "text_arabic": "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ", "text_transliteration": "Siratal ladhina anamta alayhim", "text_translation": "The path of those upon whom You have bestowed favor.", "juz": 1, "page": 1},
            ]
        },
        {
            "id": 112, "name_arabic": "الإخلاص", "name_english": "Al-Ikhlas",
            "name_translation": "The Sincerity", "ayah_count": 4, "revelation_type": "meccan",
            "ayahs": [
                {"ayah_number": 1, "text_arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ", "text_transliteration": "Qul huwa Allahu ahad", "text_translation": "Say, He is Allah, One.", "juz": 30, "page": 604},
                {"ayah_number": 2, "text_arabic": "اللَّهُ الصَّمَدُ", "text_transliteration": "Allahus samad", "text_translation": "Allah, the Eternal Refuge.", "juz": 30, "page": 604},
                {"ayah_number": 3, "text_arabic": "لَمْ يَلِدْ وَلَمْ يُولَدْ", "text_transliteration": "Lam yalid wa lam yulad", "text_translation": "He neither begets nor is born.", "juz": 30, "page": 604},
                {"ayah_number": 4, "text_arabic": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ", "text_transliteration": "Wa lam yakun lahu kufuwan ahad", "text_translation": "Nor is there to Him any equivalent.", "juz": 30, "page": 604},
            ]
        },
    ]

    for surah_entry in SURAH_SEED:
        ayahs_data = surah_entry.pop('ayahs')
        surah      = Surah(**surah_entry)
        db.session.add(surah)
        db.session.flush()
        for ayah_data in ayahs_data:
            db.session.add(Ayah(surah_id=surah.id, **ayah_data))

    collection = HadithCollection(name='Sahih al-Bukhari', name_arabic='صحيح البخاري', slug='bukhari')
    db.session.add(collection)
    db.session.flush()

    HADITHS = [
        {'hadith_number': '1', 'text_arabic': 'إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ', 'text_english': 'Actions are but by intention and every man shall have only that which he intended.', 'narrator': 'Umar ibn al-Khattab', 'grade': 'Sahih'},
        {'hadith_number': '2', 'text_arabic': None, 'text_english': 'Islam is built upon five pillars: testifying that there is no god but Allah and that Muhammad is the Messenger of Allah, establishing prayer, paying zakat, fasting Ramadan, and performing Hajj.', 'narrator': 'Abdullah ibn Umar', 'grade': 'Sahih'},
        {'hadith_number': '3', 'text_arabic': None, 'text_english': 'Religion is sincerity. We said: To whom? He said: To Allah, His Book, His Messenger, the leaders of the Muslims and their common folk.', 'narrator': 'Tamim ad-Dari', 'grade': 'Sahih'},
    ]
    for h in HADITHS:
        db.session.add(Hadith(collection_id=collection.id, **h))

    metadata = db.session.get(ContentMetadata, 1)
    if metadata is None:
        metadata = ContentMetadata(id=1, quran_updated_at=now, hadith_updated_at=now)
        db.session.add(metadata)
    else:
        metadata.quran_updated_at  = now
        metadata.hadith_updated_at = now

    db.session.commit()

    return jsonify({
        'skipped':           False,
        'surahs':            Surah.query.count(),
        'ayahs':             Ayah.query.count(),
        'collections':       HadithCollection.query.count(),
        'hadiths':           Hadith.query.count(),
        'quran_updated_at':  now.isoformat(),
        'hadith_updated_at': now.isoformat(),
    }), 200