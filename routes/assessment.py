from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import (
    AssessmentQuestion, AssessmentResult,
    LearningProfile, XPHistory
)
import json
from datetime import date

assessment_bp = Blueprint('assessment', __name__)

# ─── Level System ─────────────────────────────────────────────────────────────

LEVELS = {
    1: 'Beginner',
    2: 'Explorer',
    3: 'Growing Learner',
    4: 'Intermediate',
    5: 'Advanced',
    6: 'Expert',
    7: 'Lifelong Learner',
}

# ─── Hardcoded Assessment Questions ───────────────────────────────────────────

ASSESSMENT_QUESTIONS = [
    # Arabic Reading
    {
        "id": 1,
        "category": "arabic",
        "question": "Can you read Arabic letters?",
        "option_a": "Yes, fluently",
        "option_b": "Yes, slowly",
        "option_c": "A little",
        "option_d": "Not at all",
        "correct": "a",
        "difficulty": 1,
        "explanation": "This helps us understand your Arabic reading level."
    },
    {
        "id": 2,
        "category": "arabic",
        "question": "Which of these is the correct Arabic letter for 'B' sound (Ba)?",
        "option_a": "ب",
        "option_b": "ت",
        "option_c": "ث",
        "option_d": "ن",
        "correct": "a",
        "difficulty": 1,
        "explanation": "ب (Ba) is the Arabic letter that makes the 'B' sound."
    },
    {
        "id": 3,
        "category": "arabic",
        "question": "What does this Arabic word mean: اللَّهُ",
        "option_a": "Allah (God)",
        "option_b": "Prophet",
        "option_c": "Quran",
        "option_d": "Prayer",
        "correct": "a",
        "difficulty": 2,
        "explanation": "اللَّهُ means Allah, the name of God in Arabic."
    },

    # Tajweed
    {
        "id": 4,
        "category": "tajweed",
        "question": "What is Tajweed?",
        "option_a": "Rules for correct Quran recitation",
        "option_b": "Arabic grammar",
        "option_c": "Quran translation",
        "option_d": "Islamic history",
        "correct": "a",
        "difficulty": 1,
        "explanation": "Tajweed refers to the rules governing pronunciation during recitation of the Quran."
    },
    {
        "id": 5,
        "category": "tajweed",
        "question": "What does 'Madd' mean in Tajweed?",
        "option_a": "Prolongation of a vowel sound",
        "option_b": "Stopping at a letter",
        "option_c": "Silent letter",
        "option_d": "Heavy pronunciation",
        "correct": "a",
        "difficulty": 2,
        "explanation": "Madd refers to the elongation or stretching of a vowel sound in Quran recitation."
    },

    # Memorization
    {
        "id": 6,
        "category": "memorization",
        "question": "How many surahs have you memorized?",
        "option_a": "More than 10",
        "option_b": "5 to 10",
        "option_c": "1 to 5",
        "option_d": "None",
        "correct": "a",
        "difficulty": 1,
        "explanation": "This helps us understand your memorization level."
    },
    {
        "id": 7,
        "category": "memorization",
        "question": "Complete this ayah: 'Bismillah ir-Rahman...'",
        "option_a": "ir-Raheem",
        "option_b": "ir-Kareem",
        "option_c": "ir-Hakeem",
        "option_d": "ir-Aleem",
        "correct": "a",
        "difficulty": 1,
        "explanation": "Bismillah ir-Rahman ir-Raheem means In the name of Allah, the Most Gracious, the Most Merciful."
    },

    # Understanding
    {
        "id": 8,
        "category": "understanding",
        "question": "What is the meaning of Surah Al-Fatiha?",
        "option_a": "The Opening",
        "option_b": "The Victory",
        "option_c": "The Light",
        "option_d": "The Truth",
        "correct": "a",
        "difficulty": 1,
        "explanation": "Al-Fatiha means The Opening. It is the first surah of the Quran."
    },
    {
        "id": 9,
        "category": "understanding",
        "question": "What does 'Alhamdulillah' mean?",
        "option_a": "All praise is due to Allah",
        "option_b": "Allah is great",
        "option_c": "In the name of Allah",
        "option_d": "May Allah bless you",
        "correct": "a",
        "difficulty": 1,
        "explanation": "Alhamdulillah means All praise is due to Allah."
    },

    # Vocabulary
    {
        "id": 10,
        "category": "vocabulary",
        "question": "What does the Arabic word 'رَحْمَة' (Rahmah) mean?",
        "option_a": "Mercy",
        "option_b": "Knowledge",
        "option_c": "Power",
        "option_d": "Patience",
        "correct": "a",
        "difficulty": 2,
        "explanation": "رَحْمَة (Rahmah) means Mercy or Compassion in Arabic."
    },
    {
        "id": 11,
        "category": "vocabulary",
        "question": "What does 'صَبْر' (Sabr) mean?",
        "option_a": "Patience",
        "option_b": "Prayer",
        "option_c": "Fasting",
        "option_d": "Charity",
        "correct": "a",
        "difficulty": 2,
        "explanation": "صَبْر (Sabr) means patience or perseverance in Arabic."
    },

    # Islamic Knowledge
    {
        "id": 12,
        "category": "islamic",
        "question": "How many surahs are in the Quran?",
        "option_a": "114",
        "option_b": "112",
        "option_c": "116",
        "option_d": "110",
        "correct": "a",
        "difficulty": 1,
        "explanation": "The Quran contains 114 surahs (chapters)."
    },
    {
        "id": 13,
        "category": "islamic",
        "question": "Which surah is known as the heart of the Quran?",
        "option_a": "Surah Ya-Sin",
        "option_b": "Surah Al-Fatiha",
        "option_c": "Surah Al-Baqarah",
        "option_d": "Surah Al-Ikhlas",
        "correct": "a",
        "difficulty": 2,
        "explanation": "Surah Ya-Sin (Chapter 36) is known as the heart of the Quran."
    },
    {
        "id": 14,
        "category": "islamic",
        "question": "In which month was the Quran first revealed?",
        "option_a": "Ramadan",
        "option_b": "Muharram",
        "option_c": "Rajab",
        "option_d": "Shaban",
        "correct": "a",
        "difficulty": 1,
        "explanation": "The Quran was first revealed in the month of Ramadan."
    },
    {
        "id": 15,
        "category": "islamic",
        "question": "How many Juz (parts) does the Quran have?",
        "option_a": "30",
        "option_b": "28",
        "option_c": "32",
        "option_d": "25",
        "correct": "a",
        "difficulty": 1,
        "explanation": "The Quran is divided into 30 equal parts called Juz."
    },
]


# ─── Scoring Algorithm ────────────────────────────────────────────────────────

def calculate_scores(answers: dict) -> dict:
    """
    Calculate category scores based on user answers.
    Formula: score = (correct_in_category / total_in_category) * 100
    """
    categories = {
        'arabic':        {'correct': 0, 'total': 0},
        'tajweed':       {'correct': 0, 'total': 0},
        'memorization':  {'correct': 0, 'total': 0},
        'understanding': {'correct': 0, 'total': 0},
        'vocabulary':    {'correct': 0, 'total': 0},
        'islamic':       {'correct': 0, 'total': 0},
    }

    for q in ASSESSMENT_QUESTIONS:
        cat        = q['category']
        q_id       = str(q['id'])
        user_ans   = answers.get(q_id, '').lower().strip()
        correct    = q['correct'].lower()
        categories[cat]['total'] += 1
        if user_ans == correct:
            categories[cat]['correct'] += 1

    scores = {}
    for cat, data in categories.items():
        if data['total'] > 0:
            scores[cat] = round((data['correct'] / data['total']) * 100, 2)
        else:
            scores[cat] = 0.0

    overall = round(sum(scores.values()) / len(scores), 2)

    return {**scores, 'overall': overall}


def assign_level(overall_score: float) -> int:
    """
    Assign learning level based on overall score.
    Formula: level = score / 15 (rounded up, max 7)
    """
    if overall_score >= 90: return 7
    if overall_score >= 75: return 6
    if overall_score >= 60: return 5
    if overall_score >= 45: return 4
    if overall_score >= 30: return 3
    if overall_score >= 15: return 2
    return 1


def calculate_xp_from_assessment(scores: dict) -> int:
    """
    Base XP from assessment = overall_score * 0.5 (max 50 XP)
    """
    return min(50, int(scores['overall'] * 0.5))


# ─── Routes ───────────────────────────────────────────────────────────────────

@assessment_bp.route('/questions', methods=['GET'])
@jwt_required()
def get_questions():
    """Return all assessment questions without correct answers."""
    questions = [{
        'id':       q['id'],
        'category': q['category'],
        'question': q['question'],
        'option_a': q['option_a'],
        'option_b': q['option_b'],
        'option_c': q['option_c'],
        'option_d': q['option_d'],
    } for q in ASSESSMENT_QUESTIONS]

    return jsonify({
        'total':     len(questions),
        'questions': questions,
    }), 200


@assessment_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assessment():
    """
    Submit assessment answers and get learning profile.
    Body: {"answers": {"1": "a", "2": "b", ...}}
    """
    user_id = int(get_jwt_identity())
    data    = request.get_json(silent=True) or {}
    answers = data.get('answers', {})

    if not answers:
        return jsonify({'error': 'answers are required'}), 400

    # Calculate scores
    scores = calculate_scores(answers)
    level  = assign_level(scores['overall'])
    xp     = calculate_xp_from_assessment(scores)

    # Save assessment result
    result = AssessmentResult(
        user_id             = user_id,
        arabic_score        = scores['arabic'],
        tajweed_score       = scores['tajweed'],
        memorization_score  = scores['memorization'],
        understanding_score = scores['understanding'],
        vocabulary_score    = scores['vocabulary'],
        islamic_score       = scores['islamic'],
        overall_score       = scores['overall'],
        assigned_level      = level,
        answers             = json.dumps(answers),
    )
    db.session.add(result)

    # Create or update learning profile
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)

    profile.arabic_score        = scores['arabic']
    profile.tajweed_score       = scores['tajweed']
    profile.memorization_score  = scores['memorization']
    profile.understanding_score = scores['understanding']
    profile.vocabulary_score    = scores['vocabulary']
    profile.islamic_score       = scores['islamic']
    profile.level               = level
    profile.level_name          = LEVELS[level]
    profile.xp_total            = xp
    profile.xp_today            = xp
    profile.assessment_done     = True
    profile.last_active_date    = date.today()

    # Save XP history
    xp_entry = XPHistory(
        user_id = user_id,
        xp      = xp,
        reason  = 'Completed initial assessment',
        source  = 'assessment',
    )
    db.session.add(xp_entry)
    db.session.commit()

    # Identify weak areas
    weak_areas = [
        cat for cat, score in {
            'Arabic Reading':  scores['arabic'],
            'Tajweed':         scores['tajweed'],
            'Memorization':    scores['memorization'],
            'Understanding':   scores['understanding'],
            'Vocabulary':      scores['vocabulary'],
            'Islamic Knowledge': scores['islamic'],
        }.items() if score < 50
    ]

    # Identify strong areas
    strong_areas = [
        cat for cat, score in {
            'Arabic Reading':  scores['arabic'],
            'Tajweed':         scores['tajweed'],
            'Memorization':    scores['memorization'],
            'Understanding':   scores['understanding'],
            'Vocabulary':      scores['vocabulary'],
            'Islamic Knowledge': scores['islamic'],
        }.items() if score >= 70
    ]

    return jsonify({
        'message':      'Assessment completed successfully!',
        'scores': {
            'arabic':        scores['arabic'],
            'tajweed':       scores['tajweed'],
            'memorization':  scores['memorization'],
            'understanding': scores['understanding'],
            'vocabulary':    scores['vocabulary'],
            'islamic':       scores['islamic'],
            'overall':       scores['overall'],
        },
        'assigned_level': level,
        'level_name':     LEVELS[level],
        'xp_earned':      xp,
        'weak_areas':     weak_areas,
        'strong_areas':   strong_areas,
        'profile':        profile.to_dict(),
    }), 200


@assessment_bp.route('/result', methods=['GET'])
@jwt_required()
def get_result():
    """Get the user's latest assessment result."""
    user_id = int(get_jwt_identity())
    result  = AssessmentResult.query.filter_by(user_id=user_id).order_by(AssessmentResult.created_at.desc()).first()

    if not result:
        return jsonify({'error': 'No assessment found. Please take the assessment first.'}), 404

    return jsonify({'result': result.to_dict()}), 200


@assessment_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get the user's learning profile."""
    user_id = int(get_jwt_identity())
    profile = LearningProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({'error': 'No learning profile found. Please take the assessment first.'}), 404

    return jsonify({'profile': profile.to_dict()}), 200