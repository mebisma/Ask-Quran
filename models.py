import re
from datetime import datetime
from extensions import db, bcrypt


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── User ─────────────────────────────────────────────────────────────────────

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active     = db.Column(db.Boolean, default=True)
    is_verified   = db.Column(db.Boolean, default=False)
    last_login    = db.Column(db.DateTime, nullable=True)

    bookmarks        = db.relationship('Bookmark',        backref='user', lazy=True,    cascade='all, delete-orphan')
    reading_progress = db.relationship('ReadingProgress', backref='user', uselist=False, cascade='all, delete-orphan')
    tasbih           = db.relationship('TasbihCounter',   backref='user', uselist=False, cascade='all, delete-orphan')
    location         = db.relationship('UserLocation',    backref='user', uselist=False, cascade='all, delete-orphan')
    settings         = db.relationship('UserSettings',    backref='user', uselist=False, cascade='all, delete-orphan')
    reminders        = db.relationship('Reminder',        backref='user', lazy=True,    cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id':         self.id,
            'username':   self.username,
            'email':      self.email,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


# ─── Token Blocklist ──────────────────────────────────────────────────────────

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    id         = db.Column(db.Integer, primary_key=True)
    jti        = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Bookmark ─────────────────────────────────────────────────────────────────

VALID_CONTENT_TYPES = ('ayah', 'hadith')


class Bookmark(db.Model, TimestampMixin):
    __tablename__ = 'bookmarks'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type     = db.Column(db.String(10), nullable=False, default='ayah')
    surah            = db.Column(db.Integer, nullable=True)
    ayah             = db.Column(db.Integer, nullable=True)
    reference        = db.Column(db.String(255), nullable=True)
    translation_text = db.Column(db.Text, nullable=True)
    note             = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id':               self.id,
            'content_type':     self.content_type,
            'surah':            self.surah,
            'ayah':             self.ayah,
            'reference':        self.reference,
            'translation_text': self.translation_text,
            'note':             self.note,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'updated_at':       self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Reading Progress ─────────────────────────────────────────────────────────

class ReadingProgress(db.Model, TimestampMixin):
    __tablename__ = 'reading_progress'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    last_surah = db.Column(db.Integer, default=1)
    last_ayah  = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'last_surah': self.last_surah,
            'last_ayah':  self.last_ayah,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Tasbih Counter ───────────────────────────────────────────────────────────

class TasbihCounter(db.Model, TimestampMixin):
    __tablename__ = 'tasbih_counter'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    count   = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'count':      self.count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── User Location ────────────────────────────────────────────────────────────

class UserLocation(db.Model, TimestampMixin):
    __tablename__ = 'user_location'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    city    = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'city':       self.city,
            'country':    self.country,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── User Settings ────────────────────────────────────────────────────────────

VALID_THEMES    = ('light', 'dark')
VALID_LANGUAGES = ('en', 'ur')
DEFAULT_THEME     = 'light'
DEFAULT_FONT_SIZE = 16
MIN_FONT_SIZE     = 12
MAX_FONT_SIZE     = 24
DEFAULT_LANGUAGE  = 'en'


class UserSettings(db.Model, TimestampMixin):
    __tablename__ = 'user_settings'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    theme     = db.Column(db.String(10), nullable=False, default=DEFAULT_THEME)
    font_size = db.Column(db.Integer,    nullable=False, default=DEFAULT_FONT_SIZE)
    language  = db.Column(db.String(10), nullable=False, default=DEFAULT_LANGUAGE)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'theme':      self.theme,
            'font_size':  self.font_size,
            'language':   self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_defaults(cls, user_id):
        return cls(
            user_id=user_id,
            theme=DEFAULT_THEME,
            font_size=DEFAULT_FONT_SIZE,
            language=DEFAULT_LANGUAGE,
        )


# ─── Reminders ────────────────────────────────────────────────────────────────

VALID_DAYS          = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
DEFAULT_REPEAT_DAYS = 'mon,tue,wed,thu,fri,sat,sun'
TIME_PATTERN        = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')


class Reminder(db.Model, TimestampMixin):
    __tablename__ = 'reminders'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title       = db.Column(db.String(200), nullable=False)
    time        = db.Column(db.String(5),   nullable=False)
    repeat_days = db.Column(db.String(100), nullable=False, default=DEFAULT_REPEAT_DAYS)
    is_active   = db.Column(db.Boolean,     nullable=False, default=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'user_id':     self.user_id,
            'title':       self.title,
            'time':        self.time,
            'repeat_days': self.repeat_days,
            'is_active':   self.is_active,
            'created_at':  self.created_at.isoformat() if self.created_at else None,
            'updated_at':  self.updated_at.isoformat() if self.updated_at else None,
        }

    def repeats_on(self, day: str) -> bool:
        scheduled = {p.strip().lower() for p in self.repeat_days.split(',') if p.strip()}
        return day.lower() in scheduled


# ─── Offline Sync — Content Models ───────────────────────────────────────────

class Surah(db.Model):
    __tablename__ = 'surahs'
    id               = db.Column(db.Integer, primary_key=True)
    name_arabic      = db.Column(db.String(100), nullable=False)
    name_english     = db.Column(db.String(100), nullable=False)
    name_translation = db.Column(db.String(200), nullable=False)
    ayah_count       = db.Column(db.Integer, nullable=False)
    revelation_type  = db.Column(db.String(20), nullable=False)
    ayahs            = db.relationship('Ayah', backref='surah', lazy=True)

    def to_dict(self):
        return {
            'id':               self.id,
            'name_arabic':      self.name_arabic,
            'name_english':     self.name_english,
            'name_translation': self.name_translation,
            'ayah_count':       self.ayah_count,
            'revelation_type':  self.revelation_type,
        }


class Ayah(db.Model):
    __tablename__ = 'ayahs'
    id                   = db.Column(db.Integer, primary_key=True)
    surah_id             = db.Column(db.Integer, db.ForeignKey('surahs.id'), nullable=False)
    ayah_number          = db.Column(db.Integer, nullable=False)
    text_arabic          = db.Column(db.Text, nullable=False)
    text_transliteration = db.Column(db.Text, nullable=True)
    text_translation     = db.Column(db.Text, nullable=False)
    juz                  = db.Column(db.Integer, nullable=True)
    page                 = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id':                   self.id,
            'surah_id':             self.surah_id,
            'ayah_number':          self.ayah_number,
            'text_arabic':          self.text_arabic,
            'text_transliteration': self.text_transliteration,
            'text_translation':     self.text_translation,
            'juz':                  self.juz,
            'page':                 self.page,
        }


class HadithCollection(db.Model):
    __tablename__ = 'hadith_collections'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    name_arabic = db.Column(db.String(200), nullable=True)
    slug        = db.Column(db.String(100), unique=True, nullable=False)
    hadiths     = db.relationship('Hadith', backref='collection', lazy=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'name_arabic': self.name_arabic,
            'slug':        self.slug,
        }


class Hadith(db.Model):
    __tablename__ = 'hadiths'
    id            = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('hadith_collections.id'), nullable=False)
    hadith_number = db.Column(db.String(20), nullable=False)
    text_arabic   = db.Column(db.Text, nullable=True)
    text_english  = db.Column(db.Text, nullable=False)
    narrator      = db.Column(db.String(200), nullable=True)
    grade         = db.Column(db.String(50),  nullable=True)

    def to_dict(self):
        return {
            'id':            self.id,
            'collection_id': self.collection_id,
            'hadith_number': self.hadith_number,
            'text_arabic':   self.text_arabic,
            'text_english':  self.text_english,
            'narrator':      self.narrator,
            'grade':         self.grade,
        }


class ContentMetadata(db.Model):
    __tablename__     = 'content_metadata'
    id                = db.Column(db.Integer, primary_key=True)
    quran_updated_at  = db.Column(db.DateTime, nullable=True)
    hadith_updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id':                self.id,
            'quran_updated_at':  self.quran_updated_at.isoformat()  if self.quran_updated_at  else None,
            'hadith_updated_at': self.hadith_updated_at.isoformat() if self.hadith_updated_at else None,
        }
    # ─── Learning Profile ─────────────────────────────────────────────────────────

class LearningProfile(db.Model, TimestampMixin):
    __tablename__ = 'learning_profiles'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    level               = db.Column(db.Integer, default=1)
    level_name          = db.Column(db.String(50), default='Beginner')
    xp_total            = db.Column(db.Integer, default=0)
    xp_today            = db.Column(db.Integer, default=0)
    streak_days         = db.Column(db.Integer, default=0)
    streak_freeze       = db.Column(db.Integer, default=1)
    last_active_date    = db.Column(db.Date, nullable=True)
    arabic_score        = db.Column(db.Float, default=0.0)
    tajweed_score       = db.Column(db.Float, default=0.0)
    memorization_score  = db.Column(db.Float, default=0.0)
    understanding_score = db.Column(db.Float, default=0.0)
    vocabulary_score    = db.Column(db.Float, default=0.0)
    islamic_score       = db.Column(db.Float, default=0.0)
    daily_goal_xp       = db.Column(db.Integer, default=20)
    assessment_done     = db.Column(db.Boolean, default=False)
    lessons_completed   = db.Column(db.Integer, default=0)
    quizzes_completed   = db.Column(db.Integer, default=0)
    badges_earned       = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id':                   self.id,
            'user_id':              self.user_id,
            'level':                self.level,
            'level_name':           self.level_name,
            'xp_total':             self.xp_total,
            'xp_today':             self.xp_today,
            'streak_days':          self.streak_days,
            'streak_freeze':        self.streak_freeze,
            'last_active_date':     self.last_active_date.isoformat() if self.last_active_date else None,
            'arabic_score':         self.arabic_score,
            'tajweed_score':        self.tajweed_score,
            'memorization_score':   self.memorization_score,
            'understanding_score':  self.understanding_score,
            'vocabulary_score':     self.vocabulary_score,
            'islamic_score':        self.islamic_score,
            'daily_goal_xp':        self.daily_goal_xp,
            'assessment_done':      self.assessment_done,
            'lessons_completed':    self.lessons_completed,
            'quizzes_completed':    self.quizzes_completed,
            'badges_earned':        self.badges_earned,
        }


# ─── Assessment ───────────────────────────────────────────────────────────────

class AssessmentQuestion(db.Model, TimestampMixin):
    __tablename__ = 'assessment_questions'
    id            = db.Column(db.Integer, primary_key=True)
    category      = db.Column(db.String(50), nullable=False)
    question      = db.Column(db.Text, nullable=False)
    option_a      = db.Column(db.String(255), nullable=False)
    option_b      = db.Column(db.String(255), nullable=False)
    option_c      = db.Column(db.String(255), nullable=True)
    option_d      = db.Column(db.String(255), nullable=True)
    correct       = db.Column(db.String(1), nullable=False)
    difficulty    = db.Column(db.Integer, default=1)
    explanation   = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'category':    self.category,
            'question':    self.question,
            'option_a':    self.option_a,
            'option_b':    self.option_b,
            'option_c':    self.option_c,
            'option_d':    self.option_d,
            'difficulty':  self.difficulty,
        }


class AssessmentResult(db.Model, TimestampMixin):
    __tablename__ = 'assessment_results'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    arabic_score        = db.Column(db.Float, default=0.0)
    tajweed_score       = db.Column(db.Float, default=0.0)
    memorization_score  = db.Column(db.Float, default=0.0)
    understanding_score = db.Column(db.Float, default=0.0)
    vocabulary_score    = db.Column(db.Float, default=0.0)
    islamic_score       = db.Column(db.Float, default=0.0)
    overall_score       = db.Column(db.Float, default=0.0)
    assigned_level      = db.Column(db.Integer, default=1)
    answers             = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id':                   self.id,
            'user_id':              self.user_id,
            'arabic_score':         self.arabic_score,
            'tajweed_score':        self.tajweed_score,
            'memorization_score':   self.memorization_score,
            'understanding_score':  self.understanding_score,
            'vocabulary_score':     self.vocabulary_score,
            'islamic_score':        self.islamic_score,
            'overall_score':        self.overall_score,
            'assigned_level':       self.assigned_level,
            'created_at':           self.created_at.isoformat() if self.created_at else None,
        }


# ─── Lessons ──────────────────────────────────────────────────────────────────

class Lesson(db.Model, TimestampMixin):
    __tablename__ = 'lessons'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(200), nullable=False)
    category        = db.Column(db.String(50), nullable=False)
    level           = db.Column(db.Integer, nullable=False)
    order_index     = db.Column(db.Integer, nullable=False)
    objective       = db.Column(db.Text, nullable=False)
    content         = db.Column(db.Text, nullable=False)
    arabic_text     = db.Column(db.Text, nullable=True)
    transliteration = db.Column(db.Text, nullable=True)
    translation     = db.Column(db.Text, nullable=True)
    explanation     = db.Column(db.Text, nullable=True)
    xp_reward       = db.Column(db.Integer, default=10)
    duration_mins   = db.Column(db.Integer, default=5)
    is_active       = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id':               self.id,
            'title':            self.title,
            'category':         self.category,
            'level':            self.level,
            'order_index':      self.order_index,
            'objective':        self.objective,
            'content':          self.content,
            'arabic_text':      self.arabic_text,
            'transliteration':  self.transliteration,
            'translation':      self.translation,
            'explanation':      self.explanation,
            'xp_reward':        self.xp_reward,
            'duration_mins':    self.duration_mins,
        }


class UserLesson(db.Model, TimestampMixin):
    __tablename__ = 'user_lessons'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id   = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    status      = db.Column(db.String(20), default='not_started')
    xp_earned   = db.Column(db.Integer, default=0)
    attempts    = db.Column(db.Integer, default=0)
    score       = db.Column(db.Float, default=0.0)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'user_id':      self.user_id,
            'lesson_id':    self.lesson_id,
            'status':       self.status,
            'xp_earned':    self.xp_earned,
            'attempts':     self.attempts,
            'score':        self.score,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


# ─── Quizzes ──────────────────────────────────────────────────────────────────

class QuizQuestion(db.Model, TimestampMixin):
    __tablename__ = 'quiz_questions'
    id           = db.Column(db.Integer, primary_key=True)
    lesson_id    = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    question     = db.Column(db.Text, nullable=False)
    quiz_type    = db.Column(db.String(20), default='mcq')
    option_a     = db.Column(db.String(255), nullable=True)
    option_b     = db.Column(db.String(255), nullable=True)
    option_c     = db.Column(db.String(255), nullable=True)
    option_d     = db.Column(db.String(255), nullable=True)
    correct      = db.Column(db.String(255), nullable=False)
    explanation  = db.Column(db.Text, nullable=True)
    difficulty   = db.Column(db.Integer, default=1)
    xp_reward    = db.Column(db.Integer, default=5)

    def to_dict(self):
        return {
            'id':          self.id,
            'lesson_id':   self.lesson_id,
            'question':    self.question,
            'quiz_type':   self.quiz_type,
            'option_a':    self.option_a,
            'option_b':    self.option_b,
            'option_c':    self.option_c,
            'option_d':    self.option_d,
            'difficulty':  self.difficulty,
            'xp_reward':   self.xp_reward,
        }


class QuizAttempt(db.Model, TimestampMixin):
    __tablename__ = 'quiz_attempts'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id    = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    score        = db.Column(db.Float, default=0.0)
    total        = db.Column(db.Integer, default=0)
    correct      = db.Column(db.Integer, default=0)
    xp_earned    = db.Column(db.Integer, default=0)
    time_taken   = db.Column(db.Integer, default=0)
    is_perfect   = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'lesson_id':  self.lesson_id,
            'score':      self.score,
            'total':      self.total,
            'correct':    self.correct,
            'xp_earned':  self.xp_earned,
            'time_taken': self.time_taken,
            'is_perfect': self.is_perfect,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── XP History ───────────────────────────────────────────────────────────────

class XPHistory(db.Model, TimestampMixin):
    __tablename__ = 'xp_history'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    xp      = db.Column(db.Integer, nullable=False)
    reason  = db.Column(db.String(100), nullable=False)
    source  = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'xp':         self.xp,
            'reason':     self.reason,
            'source':     self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ─── Badges ───────────────────────────────────────────────────────────────────

class Badge(db.Model, TimestampMixin):
    __tablename__ = 'badges'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon        = db.Column(db.String(100), nullable=True)
    condition   = db.Column(db.String(100), nullable=False)
    xp_reward   = db.Column(db.Integer, default=50)

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'description': self.description,
            'icon':        self.icon,
            'condition':   self.condition,
            'xp_reward':   self.xp_reward,
        }


class UserBadge(db.Model, TimestampMixin):
    __tablename__ = 'user_badges'
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'badge_id':   self.badge_id,
            'earned_at':  self.created_at.isoformat() if self.created_at else None,
        }


# ─── Review Queue (Spaced Repetition) ────────────────────────────────────────

class ReviewQueue(db.Model, TimestampMixin):
    __tablename__ = 'review_queue'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id    = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    review_date  = db.Column(db.Date, nullable=False)
    interval     = db.Column(db.Integer, default=1)
    repetitions  = db.Column(db.Integer, default=0)
    ease_factor  = db.Column(db.Float, default=2.5)
    is_done      = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':          self.id,
            'user_id':     self.user_id,
            'lesson_id':   self.lesson_id,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'interval':    self.interval,
            'repetitions': self.repetitions,
            'is_done':     self.is_done,
        }


# ─── Learning Analytics ───────────────────────────────────────────────────────

class LearningAnalytics(db.Model, TimestampMixin):
    __tablename__ = 'learning_analytics'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date             = db.Column(db.Date, nullable=False)
    lessons_done     = db.Column(db.Integer, default=0)
    quizzes_done     = db.Column(db.Integer, default=0)
    xp_earned        = db.Column(db.Integer, default=0)
    time_spent_mins  = db.Column(db.Integer, default=0)
    accuracy         = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id':              self.id,
            'user_id':         self.user_id,
            'date':            self.date.isoformat() if self.date else None,
            'lessons_done':    self.lessons_done,
            'quizzes_done':    self.quizzes_done,
            'xp_earned':       self.xp_earned,
            'time_spent_mins': self.time_spent_mins,
            'accuracy':        self.accuracy,
        }