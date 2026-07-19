from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import (
    Lesson, UserLesson, LearningProfile,
    XPHistory, ReviewQueue, LearningAnalytics
)
from datetime import datetime, date

lessons_bp = Blueprint('lessons', __name__)

# ─── Hardcoded Lessons ────────────────────────────────────────────────────────

LESSONS_DATA = [
    # ── Level 1 — Beginner ───────────────────────────────────────────────────
    {
        "id": 1,
        "title": "Arabic Alphabet — Part 1",
        "category": "arabic",
        "level": 1,
        "order_index": 1,
        "objective": "Learn the first 10 Arabic letters",
        "content": "Arabic has 28 letters. We will start with the first 10. Each letter has a unique shape and sound. Learning these is your first step toward reading the Quran.",
        "arabic_text": "ا ب ت ث ج ح خ د ذ ر",
        "transliteration": "Alif, Ba, Ta, Tha, Jim, Ha, Kha, Dal, Dhal, Ra",
        "translation": "These are the first 10 letters of the Arabic alphabet.",
        "explanation": "Start by memorizing each letter's shape and sound. Practice writing them repeatedly.",
        "xp_reward": 10,
        "duration_mins": 5,
    },
    {
        "id": 2,
        "title": "Arabic Alphabet — Part 2",
        "category": "arabic",
        "level": 1,
        "order_index": 2,
        "objective": "Learn the next 10 Arabic letters",
        "content": "Continuing from where we left off. These 10 letters complete the middle section of the Arabic alphabet.",
        "arabic_text": "ز س ش ص ض ط ظ ع غ ف",
        "transliteration": "Zay, Sin, Shin, Sad, Dad, Ta, Dha, Ayn, Ghayn, Fa",
        "translation": "These are letters 11 to 20 of the Arabic alphabet.",
        "explanation": "Pay special attention to ص and ض as they are unique to Arabic.",
        "xp_reward": 10,
        "duration_mins": 5,
    },
    {
        "id": 3,
        "title": "Arabic Alphabet — Part 3",
        "category": "arabic",
        "level": 1,
        "order_index": 3,
        "objective": "Learn the last 8 Arabic letters",
        "content": "These are the final 8 letters of the Arabic alphabet. Once you learn these you know all 28 letters!",
        "arabic_text": "ق ك ل م ن ه و ي",
        "transliteration": "Qaf, Kaf, Lam, Mim, Nun, Ha, Waw, Ya",
        "translation": "These are the last 8 letters of the Arabic alphabet.",
        "explanation": "ق and ك both make K-like sounds but from different parts of the throat.",
        "xp_reward": 10,
        "duration_mins": 5,
    },
    {
        "id": 4,
        "title": "Arabic Vowels — Harakat",
        "category": "arabic",
        "level": 1,
        "order_index": 4,
        "objective": "Learn Arabic short vowels",
        "content": "Arabic vowels are small marks placed above or below letters. They tell you how to pronounce the letter. The three main vowels are Fathah, Kasrah and Dammah.",
        "arabic_text": "بَ بِ بُ",
        "transliteration": "Ba (Fathah), Bi (Kasrah), Bu (Dammah)",
        "translation": "The three short vowels in Arabic",
        "explanation": "Fathah (a) is above the letter. Kasrah (i) is below. Dammah (u) is above and looks like a small waw.",
        "xp_reward": 15,
        "duration_mins": 7,
    },

    # ── Level 1 — Surah Al-Fatiha ─────────────────────────────────────────────
    {
        "id": 5,
        "title": "Surah Al-Fatiha — Introduction",
        "category": "memorization",
        "level": 1,
        "order_index": 5,
        "objective": "Understand the importance of Surah Al-Fatiha",
        "content": "Surah Al-Fatiha is the opening chapter of the Quran. It has 7 ayahs and is recited in every unit of prayer. The Prophet ﷺ called it the greatest surah in the Quran.",
        "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "transliteration": "Bismillahir Rahmanir Raheem",
        "translation": "In the name of Allah, the Most Gracious, the Most Merciful.",
        "explanation": "This is the first ayah of Al-Fatiha. It is also called Basmala and is the beginning of 113 surahs.",
        "xp_reward": 15,
        "duration_mins": 5,
    },
    {
        "id": 6,
        "title": "Surah Al-Fatiha — Ayahs 1 to 4",
        "category": "memorization",
        "level": 1,
        "order_index": 6,
        "objective": "Memorize the first 4 ayahs of Al-Fatiha",
        "content": "Let us learn the first four ayahs of Al-Fatiha. Read each ayah carefully and try to memorize it.",
        "arabic_text": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ۝ الرَّحْمَٰنِ الرَّحِيمِ ۝ مَالِكِ يَوْمِ الدِّينِ",
        "transliteration": "Alhamdu lillahi rabbil alamin. Ar-rahmanir raheem. Maliki yawmid deen.",
        "translation": "All praise is due to Allah, Lord of the worlds. The Most Gracious, the Most Merciful. Sovereign of the Day of Recompense.",
        "explanation": "These ayahs establish Allah's qualities — He is the Lord, He is Merciful, and He is the Judge.",
        "xp_reward": 20,
        "duration_mins": 8,
    },
    {
        "id": 7,
        "title": "Surah Al-Fatiha — Ayahs 5 to 7",
        "category": "memorization",
        "level": 1,
        "order_index": 7,
        "objective": "Memorize the last 3 ayahs of Al-Fatiha",
        "content": "These are the final three ayahs of Al-Fatiha. They contain our prayer and request to Allah.",
        "arabic_text": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ ۝ اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ ۝ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ",
        "transliteration": "Iyyaka nabudu wa iyyaka nastaeen. Ihdinas siratal mustaqeem. Siratal ladhina anamta alayhim.",
        "translation": "It is You we worship and You we ask for help. Guide us to the straight path. The path of those upon whom You have bestowed favor.",
        "explanation": "These ayahs are a dua — we are asking Allah to guide us to the right path.",
        "xp_reward": 20,
        "duration_mins": 8,
    },

    # ── Level 1 — Understanding ───────────────────────────────────────────────
    {
        "id": 8,
        "title": "Understanding Bismillah",
        "category": "understanding",
        "level": 1,
        "order_index": 8,
        "objective": "Understand the deep meaning of Bismillah",
        "content": "Bismillah ir-Rahman ir-Raheem. This phrase has three names of Allah. Rahman means He is merciful to ALL creation. Raheem means He is especially merciful to believers.",
        "arabic_text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "transliteration": "Bismillahir Rahmanir Raheem",
        "translation": "In the name of Allah, the Most Gracious, the Most Merciful.",
        "explanation": "Muslims say Bismillah before starting anything important — eating, driving, working — as a reminder that Allah is with them.",
        "xp_reward": 15,
        "duration_mins": 6,
    },
    {
        "id": 9,
        "title": "Key Quran Vocabulary — Part 1",
        "category": "vocabulary",
        "level": 1,
        "order_index": 9,
        "objective": "Learn 10 common Quran words",
        "content": "Many words repeat throughout the Quran. Learning these core words will help you understand much more of what you read.",
        "arabic_text": "اللَّهُ — رَبّ — رَحْمَة — عِلْم — صَبْر — شُكْر — تَوْبَة — إِيمَان — هُدَى — نُور",
        "transliteration": "Allah, Rabb, Rahmah, Ilm, Sabr, Shukr, Tawbah, Iman, Huda, Nur",
        "translation": "God, Lord, Mercy, Knowledge, Patience, Gratitude, Repentance, Faith, Guidance, Light",
        "explanation": "These 10 words appear hundreds of times in the Quran. Memorize them well.",
        "xp_reward": 15,
        "duration_mins": 7,
    },
    {
        "id": 10,
        "title": "Introduction to Tajweed",
        "category": "tajweed",
        "level": 1,
        "order_index": 10,
        "objective": "Understand what Tajweed is and why it matters",
        "content": "Tajweed means to make better or to improve. In the context of Quran it means reciting each letter from its correct place with its proper characteristics. Allah commanded us to recite the Quran with Tarteel (measured recitation).",
        "arabic_text": "وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا",
        "transliteration": "Wa rattilil Qurana tarteelan",
        "translation": "And recite the Quran with measured recitation. (Surah Al-Muzzammil 73:4)",
        "explanation": "Tajweed is not just about beauty — it protects the meaning of the Quran. A wrong pronunciation can change the meaning of a word.",
        "xp_reward": 15,
        "duration_mins": 8,
    },

    # ── Level 2 — Explorer ────────────────────────────────────────────────────
    {
        "id": 11,
        "title": "Surah Al-Ikhlas — Full",
        "category": "memorization",
        "level": 2,
        "order_index": 1,
        "objective": "Memorize and understand Surah Al-Ikhlas",
        "content": "Surah Al-Ikhlas is one of the most important surahs. It describes the oneness of Allah. The Prophet ﷺ said reciting it is equal to reciting one third of the Quran.",
        "arabic_text": "قُلْ هُوَ اللَّهُ أَحَدٌ ۝ اللَّهُ الصَّمَدُ ۝ لَمْ يَلِدْ وَلَمْ يُولَدْ ۝ وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
        "transliteration": "Qul huwa Allahu ahad. Allahus samad. Lam yalid wa lam yulad. Wa lam yakun lahu kufuwan ahad.",
        "translation": "Say He is Allah, One. Allah the Eternal Refuge. He neither begets nor is born. Nor is there to Him any equivalent.",
        "explanation": "This surah teaches Tawheed — the absolute oneness of Allah. He has no parents, no children and nothing is like Him.",
        "xp_reward": 25,
        "duration_mins": 8,
    },
    {
        "id": 12,
        "title": "Surah Al-Falaq",
        "category": "memorization",
        "level": 2,
        "order_index": 2,
        "objective": "Memorize Surah Al-Falaq",
        "content": "Surah Al-Falaq is a protection surah. It is recommended to recite it morning and evening and before sleep.",
        "arabic_text": "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ ۝ مِن شَرِّ مَا خَلَقَ ۝ وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ ۝ وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ ۝ وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ",
        "transliteration": "Qul audhu bi rabbil falaq. Min sharri ma khalaq. Wa min sharri ghasiqin idha waqab. Wa min sharrin naffathati fil uqad. Wa min sharri hasidin idha hasad.",
        "translation": "Say I seek refuge in the Lord of daybreak. From the evil of that which He created. And from the evil of darkness when it settles. And from the evil of those who blow on knots. And from the evil of an envier when he envies.",
        "explanation": "This surah teaches us to seek protection from Allah against all forms of evil.",
        "xp_reward": 25,
        "duration_mins": 8,
    },
    {
        "id": 13,
        "title": "Surah An-Nas",
        "category": "memorization",
        "level": 2,
        "order_index": 3,
        "objective": "Memorize Surah An-Nas",
        "content": "Surah An-Nas is the last surah of the Quran. Together with Al-Falaq they are called Al-Muawwidhatan — the two surahs of seeking refuge.",
        "arabic_text": "قُلْ أَعُوذُ بِرَبِّ النَّاسِ ۝ مَلِكِ النَّاسِ ۝ إِلَٰهِ النَّاسِ ۝ مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ ۝ الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ ۝ مِنَ الْجِنَّةِ وَالنَّاسِ",
        "transliteration": "Qul audhu bi rabbin nas. Malikin nas. Ilahin nas. Min sharril waswasil khannas. Alladhi yuwaswisu fi sudurin nas. Minal jinnati wan nas.",
        "translation": "Say I seek refuge in the Lord of mankind. The Sovereign of mankind. The God of mankind. From the evil of the retreating whisperer. Who whispers in the breasts of mankind. From among the jinn and mankind.",
        "explanation": "This surah protects us from the whispers of Shaytan and evil influences.",
        "xp_reward": 25,
        "duration_mins": 8,
    },
]

# ─── Quiz Questions for each lesson ──────────────────────────────────────────

QUIZ_DATA = {
    1: [
        {"question": "Which letter makes the 'B' sound?", "option_a": "ب", "option_b": "ت", "option_c": "ث", "correct": "a", "explanation": "ب (Ba) makes the B sound."},
        {"question": "How many letters are in the Arabic alphabet?", "option_a": "28", "option_b": "26", "option_c": "30", "correct": "a", "explanation": "Arabic has 28 letters."},
        {"question": "Which letter is 'Alif'?", "option_a": "ا", "option_b": "ب", "option_c": "ج", "correct": "a", "explanation": "ا is Alif, the first letter."},
    ],
    2: [
        {"question": "Which letter makes the 'Z' sound?", "option_a": "ز", "option_b": "س", "option_c": "ش", "correct": "a", "explanation": "ز (Zay) makes the Z sound."},
        {"question": "Which letter is unique to Arabic with no English equivalent?", "option_a": "ع", "option_b": "س", "option_c": "ف", "correct": "a", "explanation": "ع (Ayn) is a deep throat sound unique to Arabic."},
    ],
    5: [
        {"question": "How many ayahs does Surah Al-Fatiha have?", "option_a": "7", "option_b": "5", "option_c": "9", "correct": "a", "explanation": "Al-Fatiha has 7 ayahs."},
        {"question": "What is another name for Surah Al-Fatiha?", "option_a": "Umm Al-Kitab", "option_b": "Al-Ikhlas", "option_c": "Al-Baqarah", "correct": "a", "explanation": "Al-Fatiha is also called Umm Al-Kitab meaning Mother of the Book."},
    ],
    8: [
        {"question": "What does Rahman mean?", "option_a": "Merciful to all creation", "option_b": "Most Powerful", "option_c": "All Knowing", "correct": "a", "explanation": "Rahman means the one who shows mercy to all creation."},
        {"question": "What does Raheem mean?", "option_a": "Especially merciful to believers", "option_b": "Creator of all", "option_c": "The Judge", "correct": "a", "explanation": "Raheem means especially and continuously merciful to the believers."},
    ],
    11: [
        {"question": "Surah Al-Ikhlas is equal to reciting how much of the Quran?", "option_a": "One third", "option_b": "One half", "option_c": "One quarter", "correct": "a", "explanation": "The Prophet said reciting Al-Ikhlas equals one third of the Quran."},
        {"question": "What does As-Samad mean?", "option_a": "The Eternal Refuge", "option_b": "The Creator", "option_c": "The Provider", "correct": "a", "explanation": "As-Samad means the one everyone depends on but who depends on no one."},
    ],
}


# ─── Helper: Get or create learning profile ───────────────────────────────────

def _get_profile(user_id: int) -> LearningProfile:
    profile = LearningProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = LearningProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def _get_or_create_analytics(user_id: int, today: date) -> LearningAnalytics:
    analytics = LearningAnalytics.query.filter_by(user_id=user_id, date=today).first()
    if not analytics:
        analytics = LearningAnalytics(user_id=user_id, date=today)
        db.session.add(analytics)
    return analytics


def _add_xp(user_id: int, xp: int, reason: str, source: str):
    profile          = _get_profile(user_id)
    profile.xp_total += xp
    profile.xp_today += xp
    entry = XPHistory(user_id=user_id, xp=xp, reason=reason, source=source)
    db.session.add(entry)


def _schedule_review(user_id: int, lesson_id: int):
    from datetime import timedelta
    review_date = date.today() + timedelta(days=1)
    review = ReviewQueue(
        user_id     = user_id,
        lesson_id   = lesson_id,
        review_date = review_date,
        interval    = 1,
    )
    db.session.add(review)


# ─── Routes ───────────────────────────────────────────────────────────────────

@lessons_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_lessons():
    """Get all lessons — optionally filter by level or category."""
    level    = request.args.get('level', type=int)
    category = request.args.get('category')
    user_id  = int(get_jwt_identity())

    lessons = LESSONS_DATA
    if level:
        lessons = [l for l in lessons if l['level'] == level]
    if category:
        lessons = [l for l in lessons if l['category'] == category]

    user_lessons = {
        ul.lesson_id: ul.status
        for ul in UserLesson.query.filter_by(user_id=user_id).all()
    }

    result = []
    for l in lessons:
        lesson_dict          = dict(l)
        lesson_dict['status'] = user_lessons.get(l['id'], 'not_started')
        lesson_dict['has_quiz'] = l['id'] in QUIZ_DATA
        result.append(lesson_dict)

    return jsonify({'total': len(result), 'lessons': result}), 200


@lessons_bp.route('/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_lesson(lesson_id: int):
    """Get a single lesson with full content."""
    user_id = int(get_jwt_identity())
    lesson  = next((l for l in LESSONS_DATA if l['id'] == lesson_id), None)

    if not lesson:
        return jsonify({'error': 'Lesson not found.'}), 404

    user_lesson = UserLesson.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    status      = user_lesson.status if user_lesson else 'not_started'

    return jsonify({
        'lesson':    lesson,
        'status':    status,
        'has_quiz':  lesson_id in QUIZ_DATA,
    }), 200


@lessons_bp.route('/<int:lesson_id>/start', methods=['POST'])
@jwt_required()
def start_lesson(lesson_id: int):
    """Mark a lesson as in progress."""
    user_id = int(get_jwt_identity())
    lesson  = next((l for l in LESSONS_DATA if l['id'] == lesson_id), None)

    if not lesson:
        return jsonify({'error': 'Lesson not found.'}), 404

    user_lesson = UserLesson.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not user_lesson:
        user_lesson = UserLesson(
            user_id   = user_id,
            lesson_id = lesson_id,
            status    = 'in_progress',
        )
        db.session.add(user_lesson)
    elif user_lesson.status == 'not_started':
        user_lesson.status = 'in_progress'

    db.session.commit()
    return jsonify({'message': 'Lesson started.', 'lesson': lesson}), 200


@lessons_bp.route('/<int:lesson_id>/complete', methods=['POST'])
@jwt_required()
def complete_lesson(lesson_id: int):
    """
    Mark lesson as complete and award XP.
    XP Formula:
    base_xp = lesson.xp_reward
    streak_bonus = streak_days * 2 (max 20)
    total_xp = base_xp + streak_bonus
    """
    user_id = int(get_jwt_identity())
    lesson  = next((l for l in LESSONS_DATA if l['id'] == lesson_id), None)

    if not lesson:
        return jsonify({'error': 'Lesson not found.'}), 404

    today   = date.today()
    profile = _get_profile(user_id)

    user_lesson = UserLesson.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not user_lesson:
        user_lesson = UserLesson(user_id=user_id, lesson_id=lesson_id)
        db.session.add(user_lesson)

    if user_lesson.status == 'completed':
        return jsonify({'message': 'Lesson already completed.', 'profile': profile.to_dict()}), 200

    # Calculate XP
    base_xp      = lesson['xp_reward']
    streak_bonus = min(profile.streak_days * 2, 20)
    total_xp     = base_xp + streak_bonus

    # Update user lesson
    user_lesson.status       = 'completed'
    user_lesson.xp_earned    = total_xp
    user_lesson.attempts    += 1
    user_lesson.completed_at = datetime.utcnow()

    # Update profile
    profile.lessons_completed += 1
    profile.last_active_date   = today
    _add_xp(user_id, total_xp, f'Completed lesson: {lesson["title"]}', 'lesson')

    # Update streak
    _update_streak(profile, today)

    # Schedule review (spaced repetition)
    _schedule_review(user_id, lesson_id)

    # Update analytics
    analytics              = _get_or_create_analytics(user_id, today)
    analytics.lessons_done += 1
    analytics.xp_earned   += total_xp

    # Check level up
    level_up = _check_level_up(profile)

    db.session.commit()

    return jsonify({
        'message':      'Lesson completed!',
        'xp_earned':    total_xp,
        'base_xp':      base_xp,
        'streak_bonus': streak_bonus,
        'level_up':     level_up,
        'profile':      profile.to_dict(),
        'next_lesson':  _get_next_lesson(lesson_id, profile.level),
    }), 200


@lessons_bp.route('/recommended', methods=['GET'])
@jwt_required()
def get_recommended():
    """Get recommended lessons based on user level and weak areas."""
    user_id = int(get_jwt_identity())
    profile = _get_profile(user_id)

    # Get completed lessons
    completed = {
        ul.lesson_id
        for ul in UserLesson.query.filter_by(user_id=user_id, status='completed').all()
    }

    # Find weak category
    scores = {
        'arabic':        profile.arabic_score,
        'tajweed':       profile.tajweed_score,
        'memorization':  profile.memorization_score,
        'understanding': profile.understanding_score,
        'vocabulary':    profile.vocabulary_score,
        'islamic':       profile.islamic_score,
    }
    weak_category = min(scores, key=scores.get)

    # Get lessons for user level not yet completed
    recommended = [
        l for l in LESSONS_DATA
        if l['id'] not in completed and l['level'] <= profile.level
    ]

    # Prioritize weak category
    weak_first = sorted(
        recommended,
        key=lambda l: (0 if l['category'] == weak_category else 1, l['order_index'])
    )

    return jsonify({
        'weak_category':  weak_category,
        'recommended':    weak_first[:5],
        'total_remaining': len(recommended),
    }), 200


@lessons_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    """Get user's overall lesson progress."""
    user_id     = int(get_jwt_identity())
    profile     = _get_profile(user_id)
    total       = len(LESSONS_DATA)
    completed   = UserLesson.query.filter_by(user_id=user_id, status='completed').count()
    in_progress = UserLesson.query.filter_by(user_id=user_id, status='in_progress').count()

    return jsonify({
        'total_lessons':    total,
        'completed':        completed,
        'in_progress':      in_progress,
        'not_started':      total - completed - in_progress,
        'completion_pct':   round((completed / total) * 100, 1) if total > 0 else 0,
        'profile':          profile.to_dict(),
    }), 200


@lessons_bp.route('/<int:lesson_id>/quiz', methods=['GET'])
@jwt_required()
def get_quiz(lesson_id: int):
    """Get quiz questions for a lesson."""
    questions = QUIZ_DATA.get(lesson_id)
    if not questions:
        return jsonify({'error': 'No quiz available for this lesson.'}), 404

    safe_questions = [{
        'id':       i + 1,
        'question': q['question'],
        'option_a': q['option_a'],
        'option_b': q['option_b'],
        'option_c': q.get('option_c'),
    } for i, q in enumerate(questions)]

    return jsonify({'lesson_id': lesson_id, 'questions': safe_questions}), 200


@lessons_bp.route('/<int:lesson_id>/quiz/submit', methods=['POST'])
@jwt_required()
def submit_quiz(lesson_id: int):
    """
    Submit quiz answers and get XP.
    XP Formula:
    correct_xp   = correct_answers * 5
    perfect_bonus = 15 if all correct else 0
    speed_bonus  = 5 if time_taken < 120 seconds else 0
    total_xp     = correct_xp + perfect_bonus + speed_bonus
    """
    user_id   = int(get_jwt_identity())
    questions = QUIZ_DATA.get(lesson_id)

    if not questions:
        return jsonify({'error': 'No quiz for this lesson.'}), 404

    data       = request.get_json(silent=True) or {}
    answers    = data.get('answers', {})
    time_taken = data.get('time_taken', 0)

    correct_count = 0
    results       = []
    for i, q in enumerate(questions):
        user_ans    = answers.get(str(i + 1), '').lower().strip()
        is_correct  = user_ans == q['correct'].lower()
        if is_correct:
            correct_count += 1
        results.append({
            'question':    q['question'],
            'your_answer': user_ans,
            'correct':     q['correct'],
            'is_correct':  is_correct,
            'explanation': q['explanation'],
        })

    total         = len(questions)
    score         = round((correct_count / total) * 100, 1) if total > 0 else 0
    is_perfect    = correct_count == total

    # XP calculation
    correct_xp    = correct_count * 5
    perfect_bonus = 15 if is_perfect else 0
    speed_bonus   = 5 if time_taken < 120 else 0
    total_xp      = correct_xp + perfect_bonus + speed_bonus

    today   = date.today()
    profile = _get_profile(user_id)

    # Save attempt
    attempt = QuizAttempt(
        user_id    = user_id,
        lesson_id  = lesson_id,
        score      = score,
        total      = total,
        correct    = correct_count,
        xp_earned  = total_xp,
        time_taken = time_taken,
        is_perfect = is_perfect,
    )
    db.session.add(attempt)

    profile.quizzes_completed += 1
    _add_xp(user_id, total_xp, f'Quiz completed for lesson {lesson_id}', 'quiz')

    # Update analytics
    analytics               = _get_or_create_analytics(user_id, today)
    analytics.quizzes_done += 1
    analytics.xp_earned    += total_xp
    analytics.accuracy      = round(
        (analytics.accuracy + score) / 2, 1
    )

    db.session.commit()

    return jsonify({
        'score':          score,
        'correct':        correct_count,
        'total':          total,
        'is_perfect':     is_perfect,
        'xp_earned':      total_xp,
        'correct_xp':     correct_xp,
        'perfect_bonus':  perfect_bonus,
        'speed_bonus':    speed_bonus,
        'results':        results,
        'profile':        profile.to_dict(),
    }), 200


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _update_streak(profile: LearningProfile, today: date):
    from datetime import timedelta
    last = profile.last_active_date
    if last is None:
        profile.streak_days = 1
    elif last == today:
        pass
    elif last == today - timedelta(days=1):
        profile.streak_days += 1
    else:
        if profile.streak_freeze > 0:
            profile.streak_freeze -= 1
        else:
            profile.streak_days = 1


def _check_level_up(profile: LearningProfile) -> bool:
    LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 900, 6: 1400, 7: 2000}
    LEVELS   = {1: 'Beginner', 2: 'Explorer', 3: 'Growing Learner',
                4: 'Intermediate', 5: 'Advanced', 6: 'Expert', 7: 'Lifelong Learner'}
    current  = profile.level
    if current < 7 and profile.xp_total >= LEVEL_XP.get(current + 1, 9999):
        profile.level      = current + 1
        profile.level_name = LEVELS[profile.level]
        return True
    return False


def _get_next_lesson(current_id: int, user_level: int):
    current = next((l for l in LESSONS_DATA if l['id'] == current_id), None)
    if not current:
        return None
    next_lessons = [
        l for l in LESSONS_DATA
        if l['level'] <= user_level and l['order_index'] > current['order_index']
        and l['level'] == current['level']
    ]
    return min(next_lessons, key=lambda l: l['order_index']) if next_lessons else None


# ─── Import QuizAttempt ───────────────────────────────────────────────────────
from models import QuizAttempt