import os
import shutil
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from models import Ayah, Surah, Hadith, HadithCollection

voice_search_bp = Blueprint('voice_search', __name__)

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm', '.mp4', '.mpeg', '.mpga'}


def _search_content(query: str, limit: int = 10) -> dict:
    query = query.strip()
    if not query:
        return {'ayahs': [], 'hadiths': [], 'total_results': 0}

    pattern = f'%{query}%'

    ayah_matches = (
        Ayah.query.join(Surah)
        .filter(or_(
            Ayah.text_arabic.ilike(pattern),
            Ayah.text_transliteration.ilike(pattern),
            Ayah.text_translation.ilike(pattern),
        ))
        .order_by(Surah.id, Ayah.ayah_number)
        .limit(limit).all()
    )

    hadith_matches = (
        Hadith.query
        .filter(or_(
            Hadith.text_arabic.ilike(pattern),
            Hadith.text_english.ilike(pattern),
        ))
        .order_by(Hadith.id)
        .limit(limit).all()
    )

    ayahs = [{
        'id':                   a.id,
        'type':                 'ayah',
        'reference':            f'Surah {a.surah_id}:{a.ayah_number}',
        'surah_name':           a.surah.name_english if a.surah else None,
        'text_arabic':          a.text_arabic,
        'text_transliteration': a.text_transliteration,
        'text_translation':     a.text_translation,
    } for a in ayah_matches]

    hadiths = [{
        'id':           h.id,
        'type':         'hadith',
        'reference':    f'{h.collection.name if h.collection else "Unknown"} {h.hadith_number}',
        'collection':   h.collection.name if h.collection else 'Unknown',
        'text_arabic':  h.text_arabic,
        'text_english': h.text_english,
        'narrator':     h.narrator,
        'grade':        h.grade,
    } for h in hadith_matches]

    return {
        'ayahs':         ayahs,
        'hadiths':       hadiths,
        'total_results': len(ayahs) + len(hadiths),
    }


@voice_search_bp.route('/text', methods=['POST'])
@jwt_required()
def text_search():
    """Search Quran and Hadith by text query."""
    data  = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'query is required'}), 400
    results = _search_content(query, limit=10)
    return jsonify({
        'query':   query,
        'results': results,
    }), 200


@voice_search_bp.route('/audio', methods=['POST'])
@jwt_required()
def voice_search():
    """Transcribe audio file and search Quran/Hadith. Requires ffmpeg + openai-whisper."""
    if 'audio' not in request.files:
        return jsonify({'error': "Missing 'audio' file in multipart/form-data"}), 400

    audio_file = request.files['audio']
    if not audio_file or not audio_file.filename:
        return jsonify({'error': 'No audio file selected'}), 400

    if not shutil.which('ffmpeg'):
        return jsonify({
            'error':   'ffmpeg not installed',
            'message': 'Windows: winget install ffmpeg | macOS: brew install ffmpeg | Linux: sudo apt install ffmpeg',
        }), 500

    filename  = secure_filename(audio_file.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported format. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}'}), 400

    tmp_path = None
    try:
        import whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            audio_file.save(tmp.name)
            tmp_path = Path(tmp.name)

        model  = whisper.load_model('small')
        result = model.transcribe(str(tmp_path), language=None, task='transcribe')
        text   = (result.get('text') or '').strip()
        lang   = result.get('language') or 'unknown'

        if not text:
            return jsonify({'error': 'No speech detected. Please record again with clear speech.'}), 400

    except ImportError:
        return jsonify({
            'error':   'Whisper not installed',
            'message': 'Run: pip install openai-whisper',
        }), 500
    except Exception as exc:
        return jsonify({'error': f'Transcription failed: {str(exc)}'}), 500
    finally:
        if tmp_path and tmp_path.exists():
            os.unlink(tmp_path)

    results = _search_content(text, limit=10)
    return jsonify({
        'transcribed_text':  text,
        'detected_language': lang,
        'results':           results,
    }), 200