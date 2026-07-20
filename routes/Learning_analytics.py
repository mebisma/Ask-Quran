from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import (
    LearningProfile, LearningAnalytics,
    XPHistory, UserLesson, QuizAttempt,
    ReviewQueue, UserBadge
)
from datetime import date, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

LEVEL_NAMES = {
    1: 'Beginner',        2: 'Explorer',
    3: 'Growing Learner', 4: 'Intermediate',
    5: 'Advanced',        6: 'Expert',
    7: 'Lifelong Learner'
}

LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 900, 6: 1400, 7: 2000}


def _get_profile(user_id: int) -> LearningProfile:
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def _get_date_range(days: int):
    today = date.today()
    return [today - timedelta(days=i) for i in range(days - 1, -1, -1)]


# ─── Routes ───────────────────────────────────────────────────────────────────

@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Complete learning overview — all stats in one call."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    today   = date.today()

    # XP progress to next level
    current_xp    = LEVEL_XP.get(profile.level, 0)
    next_xp       = LEVEL_XP.get(profile.level + 1, profile.xp_total)
    xp_progress   = profile.xp_total - current_xp
    xp_needed     = max(1, next_xp - current_xp)
    level_pct     = min(round((xp_progress / xp_needed) * 100, 1), 100)

    # Daily goal
    daily_pct     = min(round((profile.xp_today / max(1, profile.daily_goal_xp)) * 100, 1), 100)

    # Total quiz stats
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    total_quizzes = len(quiz_attempts)
    perfect_count = sum(1 for q in quiz_attempts if q.is_perfect)
    avg_score     = round(
        sum(q.score for q in quiz_attempts) / max(1, total_quizzes), 1
    )

    # Review stats
    pending_reviews = ReviewQueue.query.filter(
        ReviewQueue.user_id     == user_id,
        ReviewQueue.is_done     == False,
        ReviewQueue.review_date <= today,
    ).count()

    # Badges
    badges_earned = UserBadge.query.filter_by(user_id=user_id).count()

    # Skill scores
    skills = {
        'arabic':        profile.arabic_score,
        'tajweed':       profile.tajweed_score,
        'memorization':  profile.memorization_score,
        'understanding': profile.understanding_score,
        'vocabulary':    profile.vocabulary_score,
        'islamic':       profile.islamic_score,
    }

    return jsonify({
        'profile': {
            'level':          profile.level,
            'level_name':     profile.level_name,
            'xp_total':       profile.xp_total,
            'xp_today':       profile.xp_today,
            'streak_days':    profile.streak_days,
            'lessons_done':   profile.lessons_completed,
            'quizzes_done':   profile.quizzes_completed,
            'badges_earned':  badges_earned,
        },
        'level_progress': {
            'percent':     level_pct,
            'xp_progress': xp_progress,
            'xp_needed':   xp_needed,
            'next_level':  profile.level + 1 if profile.level < 7 else None,
        },
        'daily_goal': {
            'goal_xp':    profile.daily_goal_xp,
            'earned':     profile.xp_today,
            'percent':    daily_pct,
            'met':        profile.xp_today >= profile.daily_goal_xp,
        },
        'quiz_stats': {
            'total':         total_quizzes,
            'perfect':       perfect_count,
            'avg_score':     avg_score,
            'perfect_rate':  round((perfect_count / max(1, total_quizzes)) * 100, 1),
        },
        'reviews_due':  pending_reviews,
        'skills':       skills,
    }), 200


@analytics_bp.route('/daily', methods=['GET'])
@jwt_required()
def get_daily_analytics():
    """Get daily analytics for the last N days (default 7, max 30)."""
    user_id = int(get_jwt_identity())
    days    = min(int(request.args.get('days', 7)), 30)
    dates   = _get_date_range(days)

    analytics_map = {
        a.date: a
        for a in LearningAnalytics.query.filter(
            LearningAnalytics.user_id == user_id,
            LearningAnalytics.date.in_(dates),
        ).all()
    }

    daily = []
    for d in dates:
        a = analytics_map.get(d)
        daily.append({
            'date':         d.isoformat(),
            'day':          d.strftime('%a'),
            'lessons_done': a.lessons_done    if a else 0,
            'quizzes_done': a.quizzes_done    if a else 0,
            'xp_earned':    a.xp_earned       if a else 0,
            'time_spent':   a.time_spent_mins if a else 0,
            'accuracy':     a.accuracy        if a else 0,
            'active':       a is not None,
        })

    total_xp      = sum(d['xp_earned']    for d in daily)
    total_lessons = sum(d['lessons_done'] for d in daily)
    days_active   = sum(1 for d in daily if d['active'])
    avg_accuracy  = round(
        sum(d['accuracy'] for d in daily if d['accuracy'] > 0) /
        max(1, sum(1 for d in daily if d['accuracy'] > 0)), 1
    )

    return jsonify({
        'days':       days,
        'daily':      daily,
        'summary': {
            'total_xp':      total_xp,
            'total_lessons': total_lessons,
            'days_active':   days_active,
            'avg_accuracy':  avg_accuracy,
            'consistency':   round((days_active / days) * 100, 1),
        },
    }), 200


@analytics_bp.route('/skills', methods=['GET'])
@jwt_required()
def get_skill_analysis():
    """Detailed skill breakdown with progress and recommendations."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    skills = [
        {
            'name':        'Arabic Reading',
            'key':         'arabic',
            'score':       profile.arabic_score,
            'level':       _score_to_label(profile.arabic_score),
            'description': 'Ability to read Arabic letters and words',
            'tip':         'Practice writing Arabic letters daily for 5 minutes',
        },
        {
            'name':        'Tajweed',
            'key':         'tajweed',
            'score':       profile.tajweed_score,
            'level':       _score_to_label(profile.tajweed_score),
            'description': 'Correct pronunciation rules for Quran recitation',
            'tip':         'Listen to a qualified reciter and repeat after them',
        },
        {
            'name':        'Memorization',
            'key':         'memorization',
            'score':       profile.memorization_score,
            'level':       _score_to_label(profile.memorization_score),
            'description': 'Quran verse memorization ability',
            'tip':         'Repeat each ayah 7 times before moving to the next',
        },
        {
            'name':        'Understanding',
            'key':         'understanding',
            'score':       profile.understanding_score,
            'level':       _score_to_label(profile.understanding_score),
            'description': 'Comprehension of Quran meaning and context',
            'tip':         'Read the translation alongside Arabic text daily',
        },
        {
            'name':        'Vocabulary',
            'key':         'vocabulary',
            'score':       profile.vocabulary_score,
            'level':       _score_to_label(profile.vocabulary_score),
            'description': 'Arabic Quranic word knowledge',
            'tip':         'Learn 3 new Quranic words every day',
        },
        {
            'name':        'Islamic Knowledge',
            'key':         'islamic',
            'score':       profile.islamic_score,
            'level':       _score_to_label(profile.islamic_score),
            'description': 'General Islamic and Quranic knowledge',
            'tip':         'Read one Islamic article or listen to one lecture per week',
        },
    ]

    overall    = round(sum(s['score'] for s in skills) / len(skills), 1)
    weakest    = min(skills, key=lambda s: s['score'])
    strongest  = max(skills, key=lambda s: s['score'])

    return jsonify({
        'skills':          skills,
        'overall_score':   overall,
        'weakest_skill':   weakest,
        'strongest_skill': strongest,
        'level':           profile.level,
        'level_name':      profile.level_name,
    }), 200


@analytics_bp.route('/quiz-performance', methods=['GET'])
@jwt_required()
def get_quiz_performance():
    """Detailed quiz performance analysis."""
    user_id  = int(get_jwt_identity())
    attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(
        QuizAttempt.created_at.desc()
    ).all()

    if not attempts:
        return jsonify({'message': 'No quiz attempts yet.', 'attempts': []}), 200

    total         = len(attempts)
    perfect       = sum(1 for a in attempts if a.is_perfect)
    avg_score     = round(sum(a.score for a in attempts) / total, 1)
    avg_time      = round(sum(a.time_taken for a in attempts) / total, 1)
    total_xp      = sum(a.xp_earned for a in attempts)

    recent = [{
        'lesson_id':  a.lesson_id,
        'score':      a.score,
        'correct':    a.correct,
        'total':      a.total,
        'is_perfect': a.is_perfect,
        'xp_earned':  a.xp_earned,
        'time_taken': a.time_taken,
        'date':       a.created_at.isoformat() if a.created_at else None,
    } for a in attempts[:10]]

    return jsonify({
        'summary': {
            'total_attempts':  total,
            'perfect_scores':  perfect,
            'perfect_rate':    round((perfect / total) * 100, 1),
            'average_score':   avg_score,
            'average_time':    avg_time,
            'total_xp_earned': total_xp,
        },
        'recent_attempts': recent,
        'trend':           _calculate_trend([a.score for a in attempts[:7]]),
    }), 200


@analytics_bp.route('/weekly-report', methods=['GET'])
@jwt_required()
def get_weekly_report():
    """Full weekly learning report."""
    user_id    = int(get_jwt_identity())
    profile    = _get_profile(user_id)
    today      = date.today()
    week_start = today - timedelta(days=6)

    analytics = LearningAnalytics.query.filter(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.date   >= week_start,
    ).order_by(LearningAnalytics.date.asc()).all()

    total_xp       = sum(a.xp_earned      for a in analytics)
    total_lessons  = sum(a.lessons_done   for a in analytics)
    total_quizzes  = sum(a.quizzes_done   for a in analytics)
    total_time     = sum(a.time_spent_mins for a in analytics)
    days_active    = len(set(a.date for a in analytics))
    avg_accuracy   = round(
        sum(a.accuracy for a in analytics if a.accuracy > 0) /
        max(1, sum(1 for a in analytics if a.accuracy > 0)), 1
    )

    skills = {
        'Arabic Reading':    profile.arabic_score,
        'Tajweed':           profile.tajweed_score,
        'Memorization':      profile.memorization_score,
        'Understanding':     profile.understanding_score,
        'Vocabulary':        profile.vocabulary_score,
        'Islamic Knowledge': profile.islamic_score,
    }

    # Badges earned this week
    week_badges = UserBadge.query.filter(
        UserBadge.user_id    == user_id,
        UserBadge.created_at >= week_start,
    ).count()

    return jsonify({
        'period': {
            'start': week_start.isoformat(),
            'end':   today.isoformat(),
        },
        'summary': {
            'total_xp':        total_xp,
            'total_lessons':   total_lessons,
            'total_quizzes':   total_quizzes,
            'total_time_mins': total_time,
            'days_active':     days_active,
            'avg_accuracy':    avg_accuracy,
            'badges_earned':   week_badges,
            'streak':          profile.streak_days,
        },
        'skills':         skills,
        'strongest_area': max(skills, key=skills.get),
        'weakest_area':   min(skills, key=skills.get),
        'level': {
            'current':  profile.level,
            'name':     profile.level_name,
            'xp_total': profile.xp_total,
        },
        'daily_breakdown': [{
            'date':         a.date.isoformat(),
            'day':          a.date.strftime('%A'),
            'lessons_done': a.lessons_done,
            'xp_earned':    a.xp_earned,
            'accuracy':     a.accuracy,
        } for a in analytics],
    }), 200


@analytics_bp.route('/monthly-report', methods=['GET'])
@jwt_required()
def get_monthly_report():
    """Full monthly learning report."""
    user_id     = int(get_jwt_identity())
    profile     = _get_profile(user_id)
    today       = date.today()
    month_start = today.replace(day=1)

    analytics = LearningAnalytics.query.filter(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.date   >= month_start,
    ).all()

    total_xp      = sum(a.xp_earned      for a in analytics)
    total_lessons = sum(a.lessons_done   for a in analytics)
    total_quizzes = sum(a.quizzes_done   for a in analytics)
    total_time    = sum(a.time_spent_mins for a in analytics)
    days_active   = len(set(a.date for a in analytics))
    days_in_month = today.day
    consistency   = round((days_active / days_in_month) * 100, 1)

    return jsonify({
        'period': {
            'month': today.strftime('%B %Y'),
            'start': month_start.isoformat(),
            'end':   today.isoformat(),
        },
        'summary': {
            'total_xp':        total_xp,
            'total_lessons':   total_lessons,
            'total_quizzes':   total_quizzes,
            'total_time_mins': total_time,
            'days_active':     days_active,
            'days_in_month':   days_in_month,
            'consistency_pct': consistency,
            'streak':          profile.streak_days,
        },
        'level': {
            'current': profile.level,
            'name':    profile.level_name,
            'xp':      profile.xp_total,
        },
        'skills': {
            'arabic':        profile.arabic_score,
            'tajweed':       profile.tajweed_score,
            'memorization':  profile.memorization_score,
            'understanding': profile.understanding_score,
            'vocabulary':    profile.vocabulary_score,
            'islamic':       profile.islamic_score,
        },
    }), 200


@analytics_bp.route('/heatmap', methods=['GET'])
@jwt_required()
def get_heatmap():
    """Get activity heatmap for the last 30 days."""
    user_id = int(get_jwt_identity())
    dates   = _get_date_range(30)

    analytics_map = {
        a.date: a
        for a in LearningAnalytics.query.filter(
            LearningAnalytics.user_id == user_id,
            LearningAnalytics.date.in_(dates),
        ).all()
    }

    heatmap = []
    for d in dates:
        a = analytics_map.get(d)
        heatmap.append({
            'date':       d.isoformat(),
            'day':        d.strftime('%a'),
            'xp':         a.xp_earned       if a else 0,
            'lessons':    a.lessons_done    if a else 0,
            'active':     a is not None,
            'intensity':  _get_intensity(a.xp_earned if a else 0),
        })

    active_days = sum(1 for h in heatmap if h['active'])
    total_xp    = sum(h['xp'] for h in heatmap)

    return jsonify({
        'heatmap':     heatmap,
        'active_days': active_days,
        'total_xp':    total_xp,
        'consistency': round((active_days / 30) * 100, 1),
    }), 200


@analytics_bp.route('/xp-history', methods=['GET'])
@jwt_required()
def get_xp_history():
    """Get XP earning history with source breakdown."""
    user_id = int(get_jwt_identity())
    limit   = min(int(request.args.get('limit', 20)), 50)

    history = XPHistory.query.filter_by(user_id=user_id).order_by(
        XPHistory.created_at.desc()
    ).limit(limit).all()

    # XP by source
    all_xp   = XPHistory.query.filter_by(user_id=user_id).all()
    by_source = {}
    for x in all_xp:
        by_source[x.source] = by_source.get(x.source, 0) + x.xp

    return jsonify({
        'history':   [h.to_dict() for h in history],
        'by_source': by_source,
        'total_xp':  sum(by_source.values()),
    }), 200


@analytics_bp.route('/streak-history', methods=['GET'])
@jwt_required()
def get_streak_history():
    """Get streak information and milestones."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    today   = date.today()

    milestones    = [3, 7, 14, 30, 60, 90, 180, 365]
    reached       = [m for m in milestones if profile.streak_days >= m]
    next_milestone = next((m for m in milestones if m > profile.streak_days), None)

    return jsonify({
        'current_streak':    profile.streak_days,
        'streak_freeze':     profile.streak_freeze,
        'last_active':       profile.last_active_date.isoformat() if profile.last_active_date else None,
        'milestones_reached': reached,
        'next_milestone':    next_milestone,
        'days_to_next':      (next_milestone - profile.streak_days) if next_milestone else 0,
    }), 200


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _score_to_label(score: float) -> str:
    if score >= 80: return 'Excellent'
    if score >= 60: return 'Good'
    if score >= 40: return 'Average'
    if score >= 20: return 'Needs Work'
    return 'Beginner'


def _get_intensity(xp: int) -> int:
    """Return heatmap intensity 0-4 based on XP earned."""
    if xp == 0:  return 0
    if xp < 10:  return 1
    if xp < 25:  return 2
    if xp < 50:  return 3
    return 4


def _calculate_trend(scores: list) -> str:
    """Calculate if quiz scores are improving, declining or stable."""
    if len(scores) < 2:
        return 'stable'
    first_half = sum(scores[len(scores)//2:]) / max(1, len(scores) - len(scores)//2)
    second_half = sum(scores[:len(scores)//2]) / max(1, len(scores)//2)
    diff = second_half - first_half
    if diff > 5:   return 'improving'
    if diff < -5:  return 'declining'
    return 'stable'