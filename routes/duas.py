from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import random

duas_bp = Blueprint('duas', __name__)

DUAS = [
    {
        "id": 1,
        "category": "happy",
        "title": "Dua for Gratitude",
        "arabic": "الْحَمْدُ لِلَّهِ الَّذِي بِنِعْمَتِهِ تَتِمُّ الصَّالِحَاتُ",
        "transliteration": "Alhamdu lillahil-ladhi bini'matihi tatimmus-salihat",
        "english": "Praise be to Allah by whose grace good deeds are completed.",
        "when_to_read": "When something good happens to you"
    },
    {
        "id": 2,
        "category": "happy",
        "title": "Dua of Thanks",
        "arabic": "شُكْرًا لِلَّهِ",
        "transliteration": "Shukran lillah",
        "english": "Thanks be to Allah.",
        "when_to_read": "When feeling grateful"
    },
    {
        "id": 3,
        "category": "sad",
        "title": "Dua for Sorrow",
        "arabic": "إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ",
        "transliteration": "Inna lillahi wa inna ilayhi raji'un",
        "english": "Indeed, to Allah we belong and to Him we shall return.",
        "when_to_read": "When facing loss or sadness"
    },
    {
        "id": 4,
        "category": "sad",
        "title": "Dua for Relief from Sadness",
        "arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ",
        "transliteration": "Allahumma inni a'udhu bika minal-hammi wal-hazan",
        "english": "O Allah, I seek refuge in You from worry and grief.",
        "when_to_read": "When feeling sad or worried"
    },
    {
        "id": 5,
        "category": "depressed",
        "title": "Dua for Depression",
        "arabic": "اللَّهُمَّ رَحْمَتَكَ أَرْجُو فَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
        "transliteration": "Allahumma rahmataka arju fala takilni ila nafsi tarfata ayn",
        "english": "O Allah, I hope for Your mercy, do not leave me to myself even for a blink of an eye.",
        "when_to_read": "When feeling depressed or hopeless"
    },
    {
        "id": 6,
        "category": "depressed",
        "title": "Dua for Strength",
        "arabic": "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ",
        "transliteration": "Hasbunallahu wa ni'mal-wakil",
        "english": "Allah is sufficient for us and He is the best disposer of affairs.",
        "when_to_read": "When feeling overwhelmed or hopeless"
    },
    {
        "id": 7,
        "category": "anxious",
        "title": "Dua for Anxiety",
        "arabic": "اللَّهُمَّ لَا سَهْلَ إِلَّا مَا جَعَلْتَهُ سَهْلًا",
        "transliteration": "Allahumma la sahla illa ma ja'altahu sahla",
        "english": "O Allah, there is no ease except what You make easy.",
        "when_to_read": "When feeling anxious or stressed"
    },
    {
        "id": 8,
        "category": "anxious",
        "title": "Dua for Peace of Heart",
        "arabic": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        "transliteration": "Ala bidhikrillahi tatma'innul qulub",
        "english": "Verily in the remembrance of Allah do hearts find peace.",
        "when_to_read": "When heart is restless"
    },
    {
        "id": 9,
        "category": "morning",
        "title": "Morning Dua",
        "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ",
        "transliteration": "Asbahna wa asbahal mulku lillah",
        "english": "We have entered the morning and the dominion belongs to Allah.",
        "when_to_read": "Every morning when you wake up"
    },
    {
        "id": 10,
        "category": "evening",
        "title": "Evening Dua",
        "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ",
        "transliteration": "Amsayna wa amsal mulku lillah",
        "english": "We have entered the evening and the dominion belongs to Allah.",
        "when_to_read": "Every evening"
    },
    {
        "id": 11,
        "category": "before_sleep",
        "title": "Dua Before Sleep",
        "arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
        "transliteration": "Bismika Allahumma amutu wa ahya",
        "english": "In Your name O Allah, I die and I live.",
        "when_to_read": "Before going to sleep"
    },
    {
        "id": 12,
        "category": "after_sleep",
        "title": "Dua After Waking Up",
        "arabic": "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا",
        "transliteration": "Alhamdu lillahil-ladhi ahyana ba'da ma amatana",
        "english": "Praise be to Allah who gave us life after death.",
        "when_to_read": "When you wake up"
    },
    {
        "id": 13,
        "category": "forgiveness",
        "title": "Dua for Forgiveness",
        "arabic": "رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الرَّحِيمُ",
        "transliteration": "Rabbighfir li wa tub alayya innaka antat-tawwabur-rahim",
        "english": "My Lord forgive me and accept my repentance, You are the Acceptor of repentance, the Merciful.",
        "when_to_read": "When seeking forgiveness"
    },
    {
        "id": 14,
        "category": "forgiveness",
        "title": "Sayyidul Istighfar",
        "arabic": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ",
        "transliteration": "Allahumma anta rabbi la ilaha illa anta khalaqtani wa ana abduk",
        "english": "O Allah You are my Lord, there is no god but You, You created me and I am Your servant.",
        "when_to_read": "Master dua for forgiveness — morning and evening"
    },
    {
        "id": 15,
        "category": "protection",
        "title": "Dua for Protection",
        "arabic": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ",
        "transliteration": "Bismillahil-ladhi la yadurru ma'asmihi shay'un",
        "english": "In the name of Allah with whose name nothing can cause harm.",
        "when_to_read": "Morning and evening for protection"
    },
    {
        "id": 16,
        "category": "travelling",
        "title": "Dua for Travelling",
        "arabic": "سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ",
        "transliteration": "Subhanal-ladhi sakhkhara lana hadha wa ma kunna lahu muqrinin",
        "english": "Glory be to Him who has subjected this to us and we were not capable of it.",
        "when_to_read": "When starting a journey"
    },
    {
        "id": 17,
        "category": "eating",
        "title": "Dua Before Eating",
        "arabic": "بِسْمِ اللَّهِ",
        "transliteration": "Bismillah",
        "english": "In the name of Allah.",
        "when_to_read": "Before every meal"
    },
    {
        "id": 18,
        "category": "eating",
        "title": "Dua After Eating",
        "arabic": "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا",
        "transliteration": "Alhamdu lillahil-ladhi at'amana wa saqana",
        "english": "Praise be to Allah who fed us and gave us drink.",
        "when_to_read": "After every meal"
    },
    {
        "id": 19,
        "category": "sick",
        "title": "Dua When Sick",
        "arabic": "اللَّهُمَّ رَبَّ النَّاسِ أَذْهِبِ الْبَأْسَ اشْفِ أَنْتَ الشَّافِي",
        "transliteration": "Allahumma rabban-nasi adhhibil-ba'sa ishfi antash-shafi",
        "english": "O Allah Lord of mankind, remove the illness and heal, You are the Healer.",
        "when_to_read": "When you are sick or someone else is sick"
    },
    {
        "id": 20,
        "category": "exam",
        "title": "Dua for Knowledge",
        "arabic": "رَبِّ زِدْنِي عِلْمًا",
        "transliteration": "Rabbi zidni ilma",
        "english": "My Lord increase me in knowledge.",
        "when_to_read": "Before studying or exams"
    },
]


@duas_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_duas():
    return jsonify({
        'total': len(DUAS),
        'duas':  DUAS
    }), 200


@duas_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = list(set([d['category'] for d in DUAS]))
    return jsonify({'categories': sorted(categories)}), 200


@duas_bp.route('/category/<string:category>', methods=['GET'])
@jwt_required()
def get_duas_by_category(category):
    filtered = [d for d in DUAS if d['category'] == category]
    if not filtered:
        return jsonify({'error': f'No duas found for category: {category}'}), 404
    return jsonify({
        'category': category,
        'total':    len(filtered),
        'duas':     filtered
    }), 200


@duas_bp.route('/random', methods=['GET'])
@jwt_required()
def get_random_dua():
    dua = random.choice(DUAS)
    return jsonify({'dua': dua}), 200


@duas_bp.route('/<int:dua_id>', methods=['GET'])
@jwt_required()
def get_dua(dua_id):
    dua = next((d for d in DUAS if d['id'] == dua_id), None)
    if not dua:
        return jsonify({'error': 'Dua not found.'}), 404
    return jsonify({'dua': dua}), 200