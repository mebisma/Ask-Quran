from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import (
    LearningProfile, ReviewQueue,
    XPHistory, LearningAnalytics
)
from datetime import date, timedelta

revision_bp = Blueprint('revision', __name__)

# ─── Spaced Repetition Intervals (days) ──────────────────────────────────────
# Based on SM-2 algorithm adapted for Quran learning
# 1 → 3 → 7 → 14 → 30 days

INTERVALS   = [1, 3, 7, 14, 30]
LESSONS_MAP = {
    1:  {'title': 'Arabic Alphabet — Part 1',      'category': 'arabic'},
    2:  {'title': 'Arabic Alphabet — Part 2',      'category': 'arabic'},
    3:  {'title': 'Arabic Alphabet — Part 3',      'category': 'arabic'},
    4:  {'title': 'Arabic Vowels — Harakat',        'category': 'arabic'},
    5:  {'title': 'Surah Al-Fatiha — Introduction','category': 'memorization'},
    6:  {'title': 'Surah Al-Fatiha — Ayahs 1-4',   'category': 'memorization'},
    7:  {'title': 'Surah Al-Fatiha — Ayahs 5-7',   'category': 'memorization'},
    8:  {'title': 'Understanding Bismillah',        'category': 'understanding'},
    9:  {'title': 'Key Quran Vocabulary — Part 1',  'category': 'vocabulary'},
    10: {'title': 'Introduction to Tajweed',        'category': 'tajweed'},
    11: {'title': 'Surah Al-Ikhlas',                'category': 'memorization'},
    12: {'title': 'Surah Al-Falaq',                 'category': 'memorization'},
    13: {'title': 'Surah An-Nas',                   'category': 'memorization'},
}


def _get_profile(user_id: int) -> LearningProfile:
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


# ─── Routes ───────────────────────────────────────────────────────────────────

@revision_bp.route('/due', methods=['GET'])
@jwt_required()
def get_due_reviews():
    """
    Get all lessons due for review today.
    Sorted by overdue first then by lesson category.
    """
    user_id = int(get_jwt_identity())
    today   = date.today()

    reviews = ReviewQueue.query.filter(
        ReviewQueue.user_id    == user_id,
        ReviewQueue.is_done    == False,
        ReviewQueue.review_date <= today,
    ).order_by(ReviewQueue.review_date.asc()).all()

    result = []
    for r in reviews:
        lesson_info = LESSONS_MAP.get(r.lesson_id, {'title': f'Lesson {r.lesson_id}', 'category': 'unknown'})
        days_overdue = (today - r.review_date).days

        result.append({
            'review_id':    r.id,
            'lesson_id':    r.lesson_id,
            'title':        lesson_info['title'],
            'category':     lesson_info['category'],
            'review_date':  r.review_date.isoformat(),
            'days_overdue': days_overdue,
            'repetitions':  r.repetitions,
            'interval':     r.interval,
            'next_interval': INTERVALS[min(r.repetitions + 1, len(INTERVALS) - 1)],
        })

    return jsonify({
        'due_today':   len(result),
        'reviews':     result,
        'message':     f'You have {len(result)} lessons to review today!' if result else 'No reviews due today. Great job!',
    }), 200


@revision_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_reviews():
    """Get upcoming reviews for the next 7 days."""
    user_id    = int(get_jwt_identity())
    today      = date.today()
    next_week  = today + timedelta(days=7)

    reviews = ReviewQueue.query.filter(
        ReviewQueue.user_id     == user_id,
        ReviewQueue.is_done     == False,
        ReviewQueue.review_date >  today,
        ReviewQueue.review_date <= next_week,
    ).order_by(ReviewQueue.review_date.asc()).all()

    result = []
    for r in reviews:
        lesson_info = LESSONS_MAP.get(r.lesson_id, {'title': f'Lesson {r.lesson_id}', 'category': 'unknown'})
        days_until  = (r.review_date - today).days

        result.append({
            'review_id':   r.id,
            'lesson_id':   r.lesson_id,
            'title':       lesson_info['title'],
            'category':    lesson_info['category'],
            'review_date': r.review_date.isoformat(),
            'days_until':  days_until,
            'repetitions': r.repetitions,
        })

    # Group by date
    grouped = {}
    for r in result:
        d = r['review_date']
        if d not in grouped:
            grouped[d] = []
        grouped[d].append(r)

    return jsonify({
        'upcoming_count': len(result),
        'by_date':        grouped,
    }), 200


@revision_bp.route('/<int:review_id>/complete', methods=['POST'])
@jwt_required()
def complete_review(review_id: int):
    """
    Complete a review session.

    Spaced Repetition Algorithm (SM-2 simplified):
    - If remembered: move to next interval (1→3→7→14→30)
    - If not remembered: reset to interval 1
    - XP: 5 for remembered, 2 for not remembered

    Body: {"remembered": true/false, "confidence": 1-5}
    confidence: 1=very hard, 3=medium, 5=very easy
    """
    user_id = int(get_jwt_identity())
    review  = ReviewQueue.query.filter_by(id=review_id, user_id=user_id).first()

    if not review:
        return jsonify({'error': 'Review not found.'}), 404

    if review.is_done:
        return jsonify({'error': 'Review already completed.'}), 400

    data       = request.get_json(silent=True) or {}
    remembered = data.get('remembered', True)
    confidence = data.get('confidence', 3)

    if remembered:
        next_idx      = min(review.repetitions + 1, len(INTERVALS) - 1)
        next_interval = INTERVALS[next_idx]
        review.repetitions  += 1
        review.interval      = next_interval
        review.review_date   = date.today() + timedelta(days=next_interval)
        review.is_done       = review.repetitions >= len(INTERVALS)
        xp_earned            = 5 + (confidence - 1)
        message              = f'Great! Next review in {next_interval} days.'
    else:
        review.repetitions = 0
        review.interval    = 1
        review.review_date = date.today() + timedelta(days=1)
        review.is_done     = False
        xp_earned          = 2
        message            = 'No worries! We will review this again tomorrow.'

    # Award XP
    profile = _get_profile(user_id)
    profile.xp_total += xp_earned
    profile.xp_today += xp_earned
    db.session.add(XPHistory(
        user_id = user_id,
        xp      = xp_earned,
        reason  = f'Review completed: Lesson {review.lesson_id}',
        source  = 'review',
    ))

    # Update analytics
    today     = date.today()
    analytics = LearningAnalytics.query.filter_by(user_id=user_id, date=today).first()
    if not analytics:
        analytics = LearningAnalytics(user_id=user_id, date=today)
        db.session.add(analytics)
    analytics.xp_earned += xp_earned

    db.session.commit()

    return jsonify({
        'message':       message,
        'remembered':    remembered,
        'xp_earned':     xp_earned,
        'next_review':   review.review_date.isoformat() if not review.is_done else None,
        'next_interval': review.interval,
        'repetitions':   review.repetitions,
        'completed':     review.is_done,
    }), 200


@revision_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_schedule():
    """Get full revision schedule calendar."""
    user_id   = int(get_jwt_identity())
    today     = date.today()
    next_30   = today + timedelta(days=30)

    reviews = ReviewQueue.query.filter(
        ReviewQueue.user_id     == user_id,
        ReviewQueue.is_done     == False,
        ReviewQueue.review_date <= next_30,
    ).order_by(ReviewQueue.review_date.asc()).all()

    schedule = {}
    for r in reviews:
        d           = r.review_date.isoformat()
        lesson_info = LESSONS_MAP.get(r.lesson_id, {'title': f'Lesson {r.lesson_id}', 'category': 'unknown'})
        if d not in schedule:
            schedule[d] = []
        schedule[d].append({
            'review_id':   r.id,
            'lesson_id':   r.lesson_id,
            'title':       lesson_info['title'],
            'category':    lesson_info['category'],
            'repetitions': r.repetitions,
        })

    total_pending = ReviewQueue.query.filter_by(user_id=user_id, is_done=False).count()
    total_done    = ReviewQueue.query.filter_by(user_id=user_id, is_done=True).count()

    return jsonify({
        'schedule':       schedule,
        'total_pending':  total_pending,
        'total_done':     total_done,
        'next_30_days':   len(reviews),
    }), 200


@revision_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_revision_stats():
    """Get revision performance statistics."""
    user_id = int(get_jwt_identity())

    total     = ReviewQueue.query.filter_by(user_id=user_id).count()
    done      = ReviewQueue.query.filter_by(user_id=user_id, is_done=True).count()
    pending   = ReviewQueue.query.filter_by(user_id=user_id, is_done=False).count()
    today     = date.today()
    overdue   = ReviewQueue.query.filter(
        ReviewQueue.user_id     == user_id,
        ReviewQueue.is_done     == False,
        ReviewQueue.review_date <  today,
    ).count()

    mastered  = ReviewQueue.query.filter(
        ReviewQueue.user_id    == user_id,
        ReviewQueue.repetitions >= len(INTERVALS) - 1,
    ).count()

    retention = round((done / total) * 100, 1) if total > 0 else 0

    return jsonify({
        'total_reviews':   total,
        'completed':       done,
        'pending':         pending,
        'overdue':         overdue,
        'mastered':        mastered,
        'retention_rate':  retention,
        'intervals':       INTERVALS,
    }), 200


@revision_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_review():
    """Manually add a lesson to the review queue."""
    user_id   = int(get_jwt_identity())
    data      = request.get_json(silent=True) or {}
    lesson_id = data.get('lesson_id')

    if not lesson_id:
        return jsonify({'error': 'lesson_id is required'}), 400

    if lesson_id not in LESSONS_MAP:
        return jsonify({'error': 'Invalid lesson_id'}), 400

    existing = ReviewQueue.query.filter_by(
        user_id=user_id, lesson_id=lesson_id, is_done=False
    ).first()

    if existing:
        return jsonify({'message': 'Lesson already in review queue.', 'review': {
            'review_id':   existing.id,
            'review_date': existing.review_date.isoformat(),
        }}), 200

    review = ReviewQueue(
        user_id     = user_id,
        lesson_id   = lesson_id,
        review_date = date.today() + timedelta(days=1),
        interval    = 1,
        repetitions = 0,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({
        'message':     'Added to review queue.',
        'lesson':      LESSONS_MAP[lesson_id],
        'review_date': review.review_date.isoformat(),
    }), 201