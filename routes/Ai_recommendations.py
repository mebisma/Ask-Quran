from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import LearningProfile, LearningAnalytics, UserLesson, XPHistory
from datetime import date, timedelta
import os
from groq import Groq

ai_bp = Blueprint('ai', __name__)

# ─── Groq Client ──────────────────────────────────────────────────────────────

def _get_groq_client():
    return Groq(api_key=os.getenv('GROQ_API_KEY'))

# ─── Lesson Categories ────────────────────────────────────────────────────────

CATEGORIES = ['arabic', 'tajweed', 'memorization', 'understanding', 'vocabulary', 'islamic']

LEVEL_NAMES = {
    1: 'Beginner',       2: 'Explorer',
    3: 'Growing Learner', 4: 'Intermediate',
    5: 'Advanced',        6: 'Expert',
    7: 'Lifelong Learner'
}

# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_profile(user_id: int) -> LearningProfile:
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def _build_user_context(profile: LearningProfile) -> str:
    """Build a text summary of the user's learning profile for AI."""
    scores = {
        'Arabic Reading':    profile.arabic_score,
        'Tajweed':           profile.tajweed_score,
        'Memorization':      profile.memorization_score,
        'Understanding':     profile.understanding_score,
        'Vocabulary':        profile.vocabulary_score,
        'Islamic Knowledge': profile.islamic_score,
    }
    weak   = [k for k, v in scores.items() if v < 50]
    strong = [k for k, v in scores.items() if v >= 70]

    return f"""
User Learning Profile:
- Level: {profile.level} ({LEVEL_NAMES.get(profile.level, 'Beginner')})
- Total XP: {profile.xp_total}
- Current Streak: {profile.streak_days} days
- Lessons Completed: {profile.lessons_completed}
- Quizzes Completed: {profile.quizzes_completed}
- Assessment Done: {profile.assessment_done}

Skill Scores (out of 100):
- Arabic Reading: {profile.arabic_score}
- Tajweed: {profile.tajweed_score}
- Memorization: {profile.memorization_score}
- Understanding: {profile.understanding_score}
- Vocabulary: {profile.vocabulary_score}
- Islamic Knowledge: {profile.islamic_score}

Weak Areas (below 50): {', '.join(weak) if weak else 'None'}
Strong Areas (above 70): {', '.join(strong) if strong else 'None'}
"""


def _ask_groq(system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
    """Call Groq API and return response text."""
    try:
        client   = _get_groq_client()
        response = client.chat.completions.create(
            model    = 'llama-3.3-70b-versatile',
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            temperature = 0.3,
            max_tokens  = max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f'AI response unavailable: {str(e)}'


# ─── Routes ───────────────────────────────────────────────────────────────────

@ai_bp.route('/study-plan', methods=['GET'])
@jwt_required()
def get_study_plan():
    """Generate a personalized 7-day study plan using AI."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    context = _build_user_context(profile)

    system_prompt = """You are an expert Islamic education AI assistant.
You create personalized Quran learning study plans.
Keep responses concise, practical and encouraging.
Base all Quran content on authentic sources only.
Do not invent verses or hadiths."""

    user_prompt = f"""
{context}

Create a personalized 7-day Quran learning study plan for this user.
For each day suggest:
1. One main focus area
2. One specific topic to study
3. One practice activity
4. Estimated time (10-15 mins max)

Keep it simple, achievable and motivating.
Format as Day 1, Day 2... etc.
"""

    plan = _ask_groq(system_prompt, user_prompt, max_tokens=600)

    return jsonify({
        'study_plan':   plan,
        'level':        profile.level,
        'level_name':   LEVEL_NAMES.get(profile.level),
        'generated_for': date.today().isoformat(),
    }), 200


@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-powered lesson recommendations."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    context = _build_user_context(profile)

    completed_ids = {
        ul.lesson_id
        for ul in UserLesson.query.filter_by(user_id=user_id, status='completed').all()
    }

    system_prompt = """You are an Islamic education AI assistant.
You recommend Quran lessons based on the user's current knowledge level.
Be specific, practical and encouraging.
Always recommend starting with weaker areas first."""

    user_prompt = f"""
{context}
Lessons already completed: {len(completed_ids)}

Based on this profile recommend the next 3 things this user should learn.
For each recommendation explain:
1. What to learn
2. Why it is important for them specifically
3. One tip to make it easier

Keep each recommendation to 2-3 sentences.
"""

    recommendations = _ask_groq(system_prompt, user_prompt, max_tokens=500)

    # Also return structured weak area recommendations
    scores = {
        'arabic':        profile.arabic_score,
        'tajweed':       profile.tajweed_score,
        'memorization':  profile.memorization_score,
        'understanding': profile.understanding_score,
        'vocabulary':    profile.vocabulary_score,
        'islamic':       profile.islamic_score,
    }
    sorted_scores = sorted(scores.items(), key=lambda x: x[1])

    return jsonify({
        'ai_recommendations': recommendations,
        'priority_areas':     [{'category': k, 'score': v} for k, v in sorted_scores[:3]],
        'level':              profile.level,
    }), 200


@ai_bp.route('/weakness-analysis', methods=['GET'])
@jwt_required()
def get_weakness_analysis():
    """Get AI analysis of user's weak areas."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    context = _build_user_context(profile)

    system_prompt = """You are an expert Quran learning coach.
You analyze a student's weaknesses and provide actionable advice.
Be kind, encouraging and specific.
Never make the student feel bad about weak areas."""

    user_prompt = f"""
{context}

Analyze this student's weak areas and provide:
1. The most important weakness to fix first and why
2. A simple daily exercise to improve it (5 minutes or less)
3. One encouraging message to keep them motivated

Keep your response warm, Islamic in spirit and practical.
"""

    analysis = _ask_groq(system_prompt, user_prompt, max_tokens=400)

    scores = {
        'Arabic Reading':    profile.arabic_score,
        'Tajweed':           profile.tajweed_score,
        'Memorization':      profile.memorization_score,
        'Understanding':     profile.understanding_score,
        'Vocabulary':        profile.vocabulary_score,
        'Islamic Knowledge': profile.islamic_score,
    }
    weakest  = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)

    return jsonify({
        'analysis':       analysis,
        'weakest_area':   {'name': weakest,   'score': scores[weakest]},
        'strongest_area': {'name': strongest, 'score': scores[strongest]},
        'all_scores':     scores,
    }), 200


@ai_bp.route('/motivation', methods=['GET'])
@jwt_required()
def get_motivation():
    """Get a personalized motivational message."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    system_prompt = """You are a warm, encouraging Islamic mentor.
You motivate students to continue their Quran learning journey.
Use authentic Islamic wisdom and encouraging words.
Keep messages short, personal and uplifting.
Never quote Quran verses or hadiths you are not certain about."""

    user_prompt = f"""
The student has:
- Completed {profile.lessons_completed} lessons
- A {profile.streak_days} day streak
- Earned {profile.xp_total} XP
- Level: {LEVEL_NAMES.get(profile.level, 'Beginner')}

Write a short personal motivational message (3-4 sentences) for this student.
Make it feel warm, Islamic and encouraging based on their progress.
"""

    message = _ask_groq(system_prompt, user_prompt, max_tokens=200)

    return jsonify({
        'message':     message,
        'streak':      profile.streak_days,
        'level':       profile.level_name,
        'xp_total':    profile.xp_total,
    }), 200


@ai_bp.route('/explain', methods=['POST'])
@jwt_required()
def explain_concept():
    """Ask AI to explain any Quran or Islamic concept."""
    data    = request.get_json(silent=True) or {}
    concept = (data.get('concept') or '').strip()

    if not concept:
        return jsonify({'error': 'concept is required'}), 400

    if len(concept) > 200:
        return jsonify({'error': 'concept must be under 200 characters'}), 400

    system_prompt = """You are an Islamic education assistant.
You explain Quran concepts, Arabic terms and Islamic topics clearly.
Always base explanations on authentic Islamic sources.
Distinguish between what is Quranic fact and what is general explanation.
Keep explanations simple, clear and educational.
If you are not certain about something say so clearly."""

    user_prompt = f"""
Please explain this concept for a Quran learner: {concept}

Provide:
1. A clear simple explanation
2. Why it is important in Quran learning
3. One practical tip or example

Keep the response educational and under 200 words.
"""

    explanation = _ask_groq(system_prompt, user_prompt, max_tokens=300)

    return jsonify({
        'concept':     concept,
        'explanation': explanation,
    }), 200


@ai_bp.route('/lesson-feedback', methods=['POST'])
@jwt_required()
def get_lesson_feedback():
    """Get AI feedback after completing a lesson."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)
    data    = request.get_json(silent=True) or {}

    lesson_title = (data.get('lesson_title') or '').strip()
    quiz_score   = data.get('quiz_score', 0)
    time_taken   = data.get('time_taken', 0)

    if not lesson_title:
        return jsonify({'error': 'lesson_title is required'}), 400

    system_prompt = """You are a supportive Quran learning coach.
You give encouraging feedback after lessons.
Always be positive, specific and helpful.
Suggest how to improve without being discouraging."""

    user_prompt = f"""
A student just completed the lesson: {lesson_title}
Quiz Score: {quiz_score}%
Time taken: {time_taken} seconds
Student Level: {LEVEL_NAMES.get(profile.level, 'Beginner')}

Give encouraging feedback in 2-3 sentences:
1. Acknowledge their effort
2. Comment on their score specifically
3. One tip for what to focus on next
"""

    feedback = _ask_groq(system_prompt, user_prompt, max_tokens=200)

    return jsonify({
        'feedback':     feedback,
        'lesson':       lesson_title,
        'quiz_score':   quiz_score,
    }), 200


@ai_bp.route('/progress-forecast', methods=['GET'])
@jwt_required()
def get_progress_forecast():
    """Predict user's learning progress."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    today       = date.today()
    week_start  = today - timedelta(days=6)
    analytics   = LearningAnalytics.query.filter(
        LearningAnalytics.user_id == user_id,
        LearningAnalytics.date   >= week_start,
    ).all()

    avg_daily_xp      = sum(a.xp_earned for a in analytics) / max(len(analytics), 1)
    avg_daily_lessons = sum(a.lessons_done for a in analytics) / max(len(analytics), 1)
    days_active       = len(analytics)

    from models import ReviewQueue
    LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 900, 6: 1400, 7: 2000}
    next_level_xp = LEVEL_XP.get(profile.level + 1, 9999)
    xp_needed     = max(0, next_level_xp - profile.xp_total)
    days_to_next  = round(xp_needed / avg_daily_xp) if avg_daily_xp > 0 else None

    system_prompt = """You are a learning analytics AI.
You give realistic and encouraging progress forecasts.
Be honest but motivating."""

    user_prompt = f"""
Student stats:
- Current Level: {profile.level} ({LEVEL_NAMES.get(profile.level)})
- XP needed for next level: {xp_needed}
- Average daily XP this week: {round(avg_daily_xp, 1)}
- Days active this week: {days_active}/7
- Days to next level at current pace: {days_to_next if days_to_next else 'unknown'}

Write a 2-sentence forecast telling the student:
1. When they might reach the next level
2. What they can do to get there faster
"""

    forecast = _ask_groq(system_prompt, user_prompt, max_tokens=150)

    return jsonify({
        'forecast':           forecast,
        'avg_daily_xp':       round(avg_daily_xp, 1),
        'avg_daily_lessons':  round(avg_daily_lessons, 1),
        'days_active_week':   days_active,
        'xp_to_next_level':   xp_needed,
        'estimated_days':     days_to_next,
        'current_level':      profile.level,
        'next_level':         profile.level + 1 if profile.level < 7 else None,
    }), 200