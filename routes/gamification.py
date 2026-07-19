from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import (
    LearningProfile, XPHistory, Badge,
    UserBadge, LearningAnalytics
)
from datetime import date, timedelta

gamification_bp = Blueprint('gamification', __name__)

# ─── Badge Definitions ────────────────────────────────────────────────────────

BADGES = [
    {"id": 1,  "name": "First Step",        "description": "Complete your first lesson",           "icon": "🌟", "condition": "lessons_completed >= 1",  "xp_reward": 20},
    {"id": 2,  "name": "Quick Learner",      "description": "Complete 5 lessons",                  "icon": "⚡", "condition": "lessons_completed >= 5",  "xp_reward": 30},
    {"id": 3,  "name": "Dedicated Student",  "description": "Complete 10 lessons",                 "icon": "📚", "condition": "lessons_completed >= 10", "xp_reward": 50},
    {"id": 4,  "name": "Quiz Master",        "description": "Complete 10 quizzes",                 "icon": "🏆", "condition": "quizzes_completed >= 10", "xp_reward": 40},
    {"id": 5,  "name": "Perfect Score",      "description": "Get a perfect score on any quiz",     "icon": "💯", "condition": "perfect_quiz == True",    "xp_reward": 25},
    {"id": 6,  "name": "3 Day Streak",       "description": "Learn for 3 days in a row",           "icon": "🔥", "condition": "streak_days >= 3",        "xp_reward": 15},
    {"id": 7,  "name": "Week Warrior",       "description": "Learn for 7 days in a row",           "icon": "🔥", "condition": "streak_days >= 7",        "xp_reward": 30},
    {"id": 8,  "name": "Month Champion",     "description": "Learn for 30 days in a row",          "icon": "👑", "condition": "streak_days >= 30",       "xp_reward": 100},
    {"id": 9,  "name": "Explorer",           "description": "Reach Level 2",                       "icon": "🗺️", "condition": "level >= 2",              "xp_reward": 25},
    {"id": 10, "name": "Growing Learner",    "description": "Reach Level 3",                       "icon": "🌱", "condition": "level >= 3",              "xp_reward": 40},
    {"id": 11, "name": "Intermediate",       "description": "Reach Level 4",                       "icon": "📖", "condition": "level >= 4",              "xp_reward": 60},
    {"id": 12, "name": "Advanced Scholar",   "description": "Reach Level 5",                       "icon": "🎓", "condition": "level >= 5",              "xp_reward": 80},
    {"id": 13, "name": "XP Hunter",          "description": "Earn 500 total XP",                   "icon": "💎", "condition": "xp_total >= 500",         "xp_reward": 50},
    {"id": 14, "name": "XP Champion",        "description": "Earn 1000 total XP",                  "icon": "💎", "condition": "xp_total >= 1000",        "xp_reward": 100},
    {"id": 15, "name": "Assessment Done",    "description": "Complete the initial assessment",     "icon": "✅", "condition": "assessment_done == True", "xp_reward": 30},
]

# ─── Level System ─────────────────────────────────────────────────────────────

LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 900, 6: 1400, 7: 2000}
LEVEL_NAME = {
    1: 'Beginner',       2: 'Explorer',
    3: 'Growing Learner', 4: 'Intermediate',
    5: 'Advanced',        6: 'Expert',
    7: 'Lifelong Learner'
}

# ─── Daily Goals ──────────────────────────────────────────────────────────────

DAILY_GOALS = [
    {"id": 1, "xp": 10,  "label": "Casual",   "description": "10 XP per day"},
    {"id": 2, "xp": 20,  "label": "Regular",   "description": "20 XP per day"},
    {"id": 3, "xp": 30,  "label": "Serious",   "description": "30 XP per day"},
    {"id": 4, "xp": 50,  "label": "Intense",   "description": "50 XP per day"},
]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_profile(user_id: int) -> LearningProfile:
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def _check_and_award_badges(user_id: int, profile: LearningProfile, extra: dict = {}) -> list:
    """
    Check all badge conditions and award any new badges.
    Returns list of newly awarded badges.
    """
    earned_ids  = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user_id).all()}
    new_badges  = []

    for badge in BADGES:
        if badge['id'] in earned_ids:
            continue

        condition = badge['condition']
        awarded   = False

        if 'lessons_completed' in condition:
            threshold = int(condition.split('>=')[1].strip())
            awarded   = profile.lessons_completed >= threshold

        elif 'quizzes_completed' in condition:
            threshold = int(condition.split('>=')[1].strip())
            awarded   = profile.quizzes_completed >= threshold

        elif 'streak_days' in condition:
            threshold = int(condition.split('>=')[1].strip())
            awarded   = profile.streak_days >= threshold

        elif 'level' in condition:
            threshold = int(condition.split('>=')[1].strip())
            awarded   = profile.level >= threshold

        elif 'xp_total' in condition:
            threshold = int(condition.split('>=')[1].strip())
            awarded   = profile.xp_total >= threshold

        elif 'assessment_done' in condition:
            awarded = profile.assessment_done

        elif 'perfect_quiz' in condition:
            awarded = extra.get('perfect_quiz', False)

        if awarded:
            user_badge = UserBadge(user_id=user_id, badge_id=badge['id'])
            db.session.add(user_badge)
            profile.badges_earned  += 1
            profile.xp_total       += badge['xp_reward']
            profile.xp_today       += badge['xp_reward']
            db.session.add(XPHistory(
                user_id = user_id,
                xp      = badge['xp_reward'],
                reason  = f'Badge earned: {badge["name"]}',
                source  = 'badge',
            ))
            new_badges.append(badge)

    return new_badges


# ─── Routes ───────────────────────────────────────────────────────────────────

@gamification_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Main gamification dashboard showing all stats.
    """
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    today   = date.today()

    # XP to next level
    current_level    = profile.level
    next_level_xp    = LEVEL_XP.get(current_level + 1, profile.xp_total)
    current_level_xp = LEVEL_XP.get(current_level, 0)
    xp_progress      = profile.xp_total - current_level_xp
    xp_needed        = next_level_xp - current_level_xp
    level_progress   = round((xp_progress / xp_needed) * 100, 1) if xp_needed > 0 else 100

    # Daily goal progress
    daily_goal       = profile.daily_goal_xp
    daily_progress   = min(round((profile.xp_today / daily_goal) * 100, 1), 100)
    daily_goal_met   = profile.xp_today >= daily_goal

    # Weekly XP
    week_start  = today - timedelta(days=today.weekday())
    week_analytics = LearningAnalytics.query.filter(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.date >= week_start,
    ).all()
    weekly_xp = sum(a.xp_earned for a in week_analytics)
    weekly_lessons = sum(a.lessons_done for a in week_analytics)

    # Badges
    earned_badge_ids = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user_id).all()}
    earned_badges    = [b for b in BADGES if b['id'] in earned_badge_ids]

    # Streak status
    last_active    = profile.last_active_date
    streak_active  = last_active == today or last_active == today - timedelta(days=1)

    return jsonify({
        'profile': {
            'level':          profile.level,
            'level_name':     profile.level_name,
            'xp_total':       profile.xp_total,
            'xp_today':       profile.xp_today,
            'streak_days':    profile.streak_days,
            'streak_freeze':  profile.streak_freeze,
            'streak_active':  streak_active,
            'badges_earned':  profile.badges_earned,
            'lessons_completed': profile.lessons_completed,
            'quizzes_completed': profile.quizzes_completed,
        },
        'level_progress': {
            'current_level':    current_level,
            'current_level_xp': current_level_xp,
            'next_level_xp':    next_level_xp,
            'xp_progress':      xp_progress,
            'xp_needed':        xp_needed,
            'percent':          level_progress,
        },
        'daily_goal': {
            'goal_xp':       daily_goal,
            'earned_today':  profile.xp_today,
            'progress_pct':  daily_progress,
            'goal_met':      daily_goal_met,
        },
        'weekly': {
            'xp_earned':      weekly_xp,
            'lessons_done':   weekly_lessons,
        },
        'recent_badges': earned_badges[-3:],
        'skills': {
            'arabic':        profile.arabic_score,
            'tajweed':       profile.tajweed_score,
            'memorization':  profile.memorization_score,
            'understanding': profile.understanding_score,
            'vocabulary':    profile.vocabulary_score,
            'islamic':       profile.islamic_score,
        },
    }), 200


@gamification_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_badges():
    """Get all badges with earned status."""
    user_id         = int(get_jwt_identity())
    earned_badge_ids = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user_id).all()}

    result = []
    for badge in BADGES:
        b          = dict(badge)
        b['earned'] = badge['id'] in earned_badge_ids
        result.append(b)

    earned = [b for b in result if b['earned']]
    locked = [b for b in result if not b['earned']]

    return jsonify({
        'total':   len(BADGES),
        'earned':  len(earned),
        'locked':  len(locked),
        'badges':  result,
    }), 200


@gamification_bp.route('/badges/check', methods=['POST'])
@jwt_required()
def check_badges():
    """Check and award any new badges."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    data    = request.get_json(silent=True) or {}

    new_badges = _check_and_award_badges(user_id, profile, extra=data)
    db.session.commit()

    return jsonify({
        'new_badges': new_badges,
        'count':      len(new_badges),
        'profile':    profile.to_dict(),
    }), 200


@gamification_bp.route('/xp/history', methods=['GET'])
@jwt_required()
def get_xp_history():
    """Get XP earning history."""
    user_id = int(get_jwt_identity())
    history = XPHistory.query.filter_by(user_id=user_id).order_by(
        XPHistory.created_at.desc()
    ).limit(20).all()

    return jsonify({
        'history': [h.to_dict() for h in history],
    }), 200


@gamification_bp.route('/streak', methods=['GET'])
@jwt_required()
def get_streak():
    """Get streak details."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    today   = date.today()

    last_active   = profile.last_active_date
    streak_active = last_active == today or last_active == today - timedelta(days=1)

    milestones = [3, 7, 14, 30, 60, 90, 180, 365]
    next_milestone = next(
        (m for m in milestones if m > profile.streak_days), None
    )

    return jsonify({
        'streak_days':     profile.streak_days,
        'streak_active':   streak_active,
        'streak_freeze':   profile.streak_freeze,
        'last_active':     last_active.isoformat() if last_active else None,
        'next_milestone':  next_milestone,
        'days_to_milestone': (next_milestone - profile.streak_days) if next_milestone else 0,
    }), 200


@gamification_bp.route('/streak/freeze', methods=['POST'])
@jwt_required()
def use_streak_freeze():
    """Use a streak freeze to protect streak."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    if profile.streak_freeze <= 0:
        return jsonify({'error': 'No streak freezes available.'}), 400

    profile.streak_freeze     -= 1
    profile.last_active_date   = date.today()
    db.session.commit()

    return jsonify({
        'message':        'Streak freeze used.',
        'streak_days':    profile.streak_days,
        'freezes_left':   profile.streak_freeze,
    }), 200


@gamification_bp.route('/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """Get available daily goals."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    goals = []
    for g in DAILY_GOALS:
        goal          = dict(g)
        goal['active'] = g['xp'] == profile.daily_goal_xp
        goals.append(goal)

    return jsonify({
        'current_goal': profile.daily_goal_xp,
        'goals':        goals,
    }), 200


@gamification_bp.route('/goals/set', methods=['POST'])
@jwt_required()
def set_goal():
    """Set daily XP goal."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    data    = request.get_json(silent=True) or {}
    xp      = data.get('xp')

    valid_xp = [g['xp'] for g in DAILY_GOALS]
    if xp not in valid_xp:
        return jsonify({'error': f'XP goal must be one of: {valid_xp}'}), 400

    profile.daily_goal_xp = xp
    db.session.commit()

    return jsonify({
        'message':   'Daily goal updated.',
        'daily_goal': xp,
    }), 200


@gamification_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Get top learners by XP."""
    from models import User
    profiles = LearningProfile.query.order_by(
        LearningProfile.xp_total.desc()
    ).limit(10).all()

    leaderboard = []
    for i, p in enumerate(profiles):
        user = User.query.get(p.user_id)
        if user:
            leaderboard.append({
                'rank':           i + 1,
                'username':       user.username,
                'level':          p.level,
                'level_name':     p.level_name,
                'xp_total':       p.xp_total,
                'streak_days':    p.streak_days,
                'badges_earned':  p.badges_earned,
            })

    return jsonify({'leaderboard': leaderboard}), 200


@gamification_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get learning analytics for last 7 days."""
    user_id = int(get_jwt_identity())
    today   = date.today()
    week    = [today - timedelta(days=i) for i in range(6, -1, -1)]

    analytics_map = {
        a.date: a
        for a in LearningAnalytics.query.filter(
            LearningAnalytics.user_id == user_id,
            LearningAnalytics.date.in_(week),
        ).all()
    }

    daily = []
    for d in week:
        a = analytics_map.get(d)
        daily.append({
            'date':          d.isoformat(),
            'lessons_done':  a.lessons_done if a else 0,
            'quizzes_done':  a.quizzes_done if a else 0,
            'xp_earned':     a.xp_earned    if a else 0,
            'time_spent':    a.time_spent_mins if a else 0,
            'accuracy':      a.accuracy      if a else 0,
        })

    total_xp      = sum(d['xp_earned']    for d in daily)
    total_lessons = sum(d['lessons_done'] for d in daily)
    avg_accuracy  = round(
        sum(d['accuracy'] for d in daily if d['accuracy'] > 0) /
        max(1, sum(1 for d in daily if d['accuracy'] > 0)), 1
    )

    return jsonify({
        'daily':          daily,
        'weekly_summary': {
            'total_xp':      total_xp,
            'total_lessons': total_lessons,
            'avg_accuracy':  avg_accuracy,
        },
    }), 200


@gamification_bp.route('/weekly-report', methods=['GET'])
@jwt_required()
def get_weekly_report():
    """Get detailed weekly learning report."""
    user_id    = int(get_jwt_identity())
    profile    = _get_profile(user_id)
    today      = date.today()
    week_start = today - timedelta(days=6)

    analytics = LearningAnalytics.query.filter(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.date >= week_start,
    ).all()

    total_xp      = sum(a.xp_earned      for a in analytics)
    total_lessons = sum(a.lessons_done   for a in analytics)
    total_quizzes = sum(a.quizzes_done   for a in analytics)
    total_time    = sum(a.time_spent_mins for a in analytics)
    days_active   = len(analytics)
    avg_accuracy  = round(
        sum(a.accuracy for a in analytics if a.accuracy > 0) /
        max(1, sum(1 for a in analytics if a.accuracy > 0)), 1
    )

    # Skill progress
    skills = {
        'Arabic Reading':  profile.arabic_score,
        'Tajweed':         profile.tajweed_score,
        'Memorization':    profile.memorization_score,
        'Understanding':   profile.understanding_score,
        'Vocabulary':      profile.vocabulary_score,
        'Islamic Knowledge': profile.islamic_score,
    }
    strongest = max(skills, key=skills.get)
    weakest   = min(skills, key=skills.get)

    return jsonify({
        'week':           f'{week_start.isoformat()} to {today.isoformat()}',
        'summary': {
            'total_xp':       total_xp,
            'total_lessons':  total_lessons,
            'total_quizzes':  total_quizzes,
            'total_time_mins': total_time,
            'days_active':    days_active,
            'avg_accuracy':   avg_accuracy,
            'streak':         profile.streak_days,
        },
        'skills':         skills,
        'strongest_area': strongest,
        'weakest_area':   weakest,
        'level':          profile.level,
        'level_name':     profile.level_name,
        'badges_earned':  profile.badges_earned,
    }), 200