from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

names_bp = Blueprint('names', __name__)

# ─── 99 Names of Allah ───────────────────────────────────────────────────────

ALLAH_NAMES = [
    {"number": 1,  "arabic": "الرَّحْمَنُ", "transliteration": "Ar-Rahman",    "meaning": "The Most Gracious"},
    {"number": 2,  "arabic": "الرَّحِيمُ",  "transliteration": "Ar-Raheem",    "meaning": "The Most Merciful"},
    {"number": 3,  "arabic": "الْمَلِكُ",   "transliteration": "Al-Malik",     "meaning": "The King"},
    {"number": 4,  "arabic": "الْقُدُّوسُ", "transliteration": "Al-Quddus",    "meaning": "The Most Holy"},
    {"number": 5,  "arabic": "السَّلَامُ",  "transliteration": "As-Salam",     "meaning": "The Source of Peace"},
    {"number": 6,  "arabic": "الْمُؤْمِنُ", "transliteration": "Al-Mumin",     "meaning": "The Guardian of Faith"},
    {"number": 7,  "arabic": "الْمُهَيْمِنُ","transliteration": "Al-Muhaymin", "meaning": "The Protector"},
    {"number": 8,  "arabic": "الْعَزِيزُ",  "transliteration": "Al-Aziz",      "meaning": "The Almighty"},
    {"number": 9,  "arabic": "الْجَبَّارُ", "transliteration": "Al-Jabbar",    "meaning": "The Compeller"},
    {"number": 10, "arabic": "الْمُتَكَبِّرُ","transliteration": "Al-Mutakabbir","meaning": "The Supreme"},
    {"number": 11, "arabic": "الْخَالِقُ",  "transliteration": "Al-Khaliq",    "meaning": "The Creator"},
    {"number": 12, "arabic": "الْبَارِئُ",  "transliteration": "Al-Bari",      "meaning": "The Originator"},
    {"number": 13, "arabic": "الْمُصَوِّرُ","transliteration": "Al-Musawwir",  "meaning": "The Fashioner"},
    {"number": 14, "arabic": "الْغَفَّارُ", "transliteration": "Al-Ghaffar",   "meaning": "The Forgiving"},
    {"number": 15, "arabic": "الْقَهَّارُ", "transliteration": "Al-Qahhar",    "meaning": "The Subduer"},
    {"number": 16, "arabic": "الْوَهَّابُ", "transliteration": "Al-Wahhab",    "meaning": "The Bestower"},
    {"number": 17, "arabic": "الرَّزَّاقُ", "transliteration": "Ar-Razzaq",    "meaning": "The Provider"},
    {"number": 18, "arabic": "الْفَتَّاحُ", "transliteration": "Al-Fattah",    "meaning": "The Opener"},
    {"number": 19, "arabic": "الْعَلِيمُ",  "transliteration": "Al-Alim",      "meaning": "The All-Knowing"},
    {"number": 20, "arabic": "الْقَابِضُ",  "transliteration": "Al-Qabid",     "meaning": "The Withholder"},
    {"number": 21, "arabic": "الْبَاسِطُ",  "transliteration": "Al-Basit",     "meaning": "The Extender"},
    {"number": 22, "arabic": "الْخَافِضُ",  "transliteration": "Al-Khafid",    "meaning": "The Abaser"},
    {"number": 23, "arabic": "الرَّافِعُ",  "transliteration": "Ar-Rafi",      "meaning": "The Exalter"},
    {"number": 24, "arabic": "الْمُعِزُّ",  "transliteration": "Al-Muizz",     "meaning": "The Honourer"},
    {"number": 25, "arabic": "الْمُذِلُّ",  "transliteration": "Al-Mudhill",   "meaning": "The Humiliator"},
    {"number": 26, "arabic": "السَّمِيعُ",  "transliteration": "As-Sami",      "meaning": "The All-Hearing"},
    {"number": 27, "arabic": "الْبَصِيرُ",  "transliteration": "Al-Basir",     "meaning": "The All-Seeing"},
    {"number": 28, "arabic": "الْحَكَمُ",   "transliteration": "Al-Hakam",     "meaning": "The Judge"},
    {"number": 29, "arabic": "الْعَدْلُ",   "transliteration": "Al-Adl",       "meaning": "The Just"},
    {"number": 30, "arabic": "اللَّطِيفُ",  "transliteration": "Al-Latif",     "meaning": "The Subtle One"},
    {"number": 31, "arabic": "الْخَبِيرُ",  "transliteration": "Al-Khabir",    "meaning": "The All-Aware"},
    {"number": 32, "arabic": "الْحَلِيمُ",  "transliteration": "Al-Halim",     "meaning": "The Forbearing"},
    {"number": 33, "arabic": "الْعَظِيمُ",  "transliteration": "Al-Azim",      "meaning": "The Magnificent"},
    {"number": 34, "arabic": "الْغَفُورُ",  "transliteration": "Al-Ghafur",    "meaning": "The Forgiving"},
    {"number": 35, "arabic": "الشَّكُورُ",  "transliteration": "Ash-Shakur",   "meaning": "The Appreciative"},
    {"number": 36, "arabic": "الْعَلِيُّ",  "transliteration": "Al-Ali",       "meaning": "The Most High"},
    {"number": 37, "arabic": "الْكَبِيرُ",  "transliteration": "Al-Kabir",     "meaning": "The Most Great"},
    {"number": 38, "arabic": "الْحَفِيظُ",  "transliteration": "Al-Hafiz",     "meaning": "The Preserver"},
    {"number": 39, "arabic": "الْمُقِيتُ",  "transliteration": "Al-Muqit",     "meaning": "The Nourisher"},
    {"number": 40, "arabic": "الْحَسِيبُ",  "transliteration": "Al-Hasib",     "meaning": "The Reckoner"},
    {"number": 41, "arabic": "الْجَلِيلُ",  "transliteration": "Al-Jalil",     "meaning": "The Majestic"},
    {"number": 42, "arabic": "الْكَرِيمُ",  "transliteration": "Al-Karim",     "meaning": "The Generous"},
    {"number": 43, "arabic": "الرَّقِيبُ",  "transliteration": "Ar-Raqib",     "meaning": "The Watchful"},
    {"number": 44, "arabic": "الْمُجِيبُ",  "transliteration": "Al-Mujib",     "meaning": "The Responsive"},
    {"number": 45, "arabic": "الْوَاسِعُ",  "transliteration": "Al-Wasi",      "meaning": "The All-Encompassing"},
    {"number": 46, "arabic": "الْحَكِيمُ",  "transliteration": "Al-Hakim",     "meaning": "The Wise"},
    {"number": 47, "arabic": "الْوَدُودُ",  "transliteration": "Al-Wadud",     "meaning": "The Loving"},
    {"number": 48, "arabic": "الْمَجِيدُ",  "transliteration": "Al-Majid",     "meaning": "The Glorious"},
    {"number": 49, "arabic": "الْبَاعِثُ",  "transliteration": "Al-Baith",     "meaning": "The Resurrector"},
    {"number": 50, "arabic": "الشَّهِيدُ",  "transliteration": "Ash-Shahid",   "meaning": "The Witness"},
    {"number": 51, "arabic": "الْحَقُّ",    "transliteration": "Al-Haqq",      "meaning": "The Truth"},
    {"number": 52, "arabic": "الْوَكِيلُ",  "transliteration": "Al-Wakil",     "meaning": "The Trustee"},
    {"number": 53, "arabic": "الْقَوِيُّ",  "transliteration": "Al-Qawiyy",    "meaning": "The Most Strong"},
    {"number": 54, "arabic": "الْمَتِينُ",  "transliteration": "Al-Matin",     "meaning": "The Firm"},
    {"number": 55, "arabic": "الْوَلِيُّ",  "transliteration": "Al-Waliyy",    "meaning": "The Protecting Friend"},
    {"number": 56, "arabic": "الْحَمِيدُ",  "transliteration": "Al-Hamid",     "meaning": "The Praiseworthy"},
    {"number": 57, "arabic": "الْمُحْصِي",  "transliteration": "Al-Muhsi",     "meaning": "The Counter"},
    {"number": 58, "arabic": "الْمُبْدِئُ", "transliteration": "Al-Mubdi",     "meaning": "The Originator"},
    {"number": 59, "arabic": "الْمُعِيدُ",  "transliteration": "Al-Muid",      "meaning": "The Restorer"},
    {"number": 60, "arabic": "الْمُحْيِي",  "transliteration": "Al-Muhyi",     "meaning": "The Giver of Life"},
    {"number": 61, "arabic": "الْمُمِيتُ",  "transliteration": "Al-Mumit",     "meaning": "The Taker of Life"},
    {"number": 62, "arabic": "الْحَيُّ",    "transliteration": "Al-Hayy",      "meaning": "The Ever-Living"},
    {"number": 63, "arabic": "الْقَيُّومُ", "transliteration": "Al-Qayyum",    "meaning": "The Self-Subsisting"},
    {"number": 64, "arabic": "الْوَاجِدُ",  "transliteration": "Al-Wajid",     "meaning": "The Finder"},
    {"number": 65, "arabic": "الْمَاجِدُ",  "transliteration": "Al-Majid",     "meaning": "The Noble"},
    {"number": 66, "arabic": "الْوَاحِدُ",  "transliteration": "Al-Wahid",     "meaning": "The One"},
    {"number": 67, "arabic": "الْأَحَدُ",   "transliteration": "Al-Ahad",      "meaning": "The Unique"},
    {"number": 68, "arabic": "الصَّمَدُ",   "transliteration": "As-Samad",     "meaning": "The Eternal"},
    {"number": 69, "arabic": "الْقَادِرُ",  "transliteration": "Al-Qadir",     "meaning": "The Able"},
    {"number": 70, "arabic": "الْمُقْتَدِرُ","transliteration": "Al-Muqtadir", "meaning": "The Powerful"},
    {"number": 71, "arabic": "الْمُقَدِّمُ","transliteration": "Al-Muqaddim",  "meaning": "The Expediter"},
    {"number": 72, "arabic": "الْمُؤَخِّرُ","transliteration": "Al-Muakhkhir", "meaning": "The Delayer"},
    {"number": 73, "arabic": "الْأَوَّلُ",  "transliteration": "Al-Awwal",     "meaning": "The First"},
    {"number": 74, "arabic": "الْآخِرُ",    "transliteration": "Al-Akhir",     "meaning": "The Last"},
    {"number": 75, "arabic": "الظَّاهِرُ",  "transliteration": "Az-Zahir",     "meaning": "The Manifest"},
    {"number": 76, "arabic": "الْبَاطِنُ",  "transliteration": "Al-Batin",     "meaning": "The Hidden"},
    {"number": 77, "arabic": "الْوَالِي",   "transliteration": "Al-Wali",      "meaning": "The Governor"},
    {"number": 78, "arabic": "الْمُتَعَالِ","transliteration": "Al-Mutaali",   "meaning": "The Most Exalted"},
    {"number": 79, "arabic": "الْبَرُّ",    "transliteration": "Al-Barr",      "meaning": "The Source of Goodness"},
    {"number": 80, "arabic": "التَّوَّابُ", "transliteration": "At-Tawwab",    "meaning": "The Acceptor of Repentance"},
    {"number": 81, "arabic": "الْمُنْتَقِمُ","transliteration": "Al-Muntaqim", "meaning": "The Avenger"},
    {"number": 82, "arabic": "الْعَفُوُّ",  "transliteration": "Al-Afuww",     "meaning": "The Pardoner"},
    {"number": 83, "arabic": "الرَّؤُوفُ",  "transliteration": "Ar-Rauf",      "meaning": "The Compassionate"},
    {"number": 84, "arabic": "مَالِكُ الْمُلْكِ","transliteration": "Malik-ul-Mulk","meaning": "Owner of All Sovereignty"},
    {"number": 85, "arabic": "ذُو الْجَلَالِ","transliteration": "Dhul-Jalali-wal-Ikram","meaning": "Lord of Majesty and Bounty"},
    {"number": 86, "arabic": "الْمُقْسِطُ", "transliteration": "Al-Muqsit",    "meaning": "The Equitable"},
    {"number": 87, "arabic": "الْجَامِعُ",  "transliteration": "Al-Jami",      "meaning": "The Gatherer"},
    {"number": 88, "arabic": "الْغَنِيُّ",  "transliteration": "Al-Ghani",     "meaning": "The Self-Sufficient"},
    {"number": 89, "arabic": "الْمُغْنِي",  "transliteration": "Al-Mughni",    "meaning": "The Enricher"},
    {"number": 90, "arabic": "الْمَانِعُ",  "transliteration": "Al-Mani",      "meaning": "The Preventer"},
    {"number": 91, "arabic": "الضَّارُّ",   "transliteration": "Ad-Darr",      "meaning": "The Distresser"},
    {"number": 92, "arabic": "النَّافِعُ",  "transliteration": "An-Nafi",      "meaning": "The Benefiter"},
    {"number": 93, "arabic": "النُّورُ",    "transliteration": "An-Nur",       "meaning": "The Light"},
    {"number": 94, "arabic": "الْهَادِي",   "transliteration": "Al-Hadi",      "meaning": "The Guide"},
    {"number": 95, "arabic": "الْبَدِيعُ",  "transliteration": "Al-Badi",      "meaning": "The Originator"},
    {"number": 96, "arabic": "الْبَاقِي",   "transliteration": "Al-Baqi",      "meaning": "The Everlasting"},
    {"number": 97, "arabic": "الْوَارِثُ",  "transliteration": "Al-Warith",    "meaning": "The Inheritor"},
    {"number": 98, "arabic": "الرَّشِيدُ",  "transliteration": "Ar-Rashid",    "meaning": "The Guide to the Right Path"},
    {"number": 99, "arabic": "الصَّبُورُ",  "transliteration": "As-Sabur",     "meaning": "The Patient"},
]

# ─── 25 Prophets ─────────────────────────────────────────────────────────────

PROPHETS = [
    {"number": 1,  "arabic": "آدم",         "name": "Adam",       "meaning": "Father of mankind"},
    {"number": 2,  "arabic": "إِدْرِيس",    "name": "Idris",      "meaning": "The learned one"},
    {"number": 3,  "arabic": "نُوح",        "name": "Nuh",        "meaning": "The grateful one"},
    {"number": 4,  "arabic": "هُود",        "name": "Hud",        "meaning": "Sent to people of Ad"},
    {"number": 5,  "arabic": "صَالِح",      "name": "Salih",      "meaning": "Sent to people of Thamud"},
    {"number": 6,  "arabic": "إِبْرَاهِيم", "name": "Ibrahim",    "meaning": "Father of prophets"},
    {"number": 7,  "arabic": "لُوط",        "name": "Lut",        "meaning": "Nephew of Ibrahim"},
    {"number": 8,  "arabic": "إِسْمَاعِيل", "name": "Ismail",     "meaning": "Son of Ibrahim"},
    {"number": 9,  "arabic": "إِسْحَاق",    "name": "Ishaq",      "meaning": "Son of Ibrahim"},
    {"number": 10, "arabic": "يَعْقُوب",    "name": "Yaqub",      "meaning": "Son of Ishaq"},
    {"number": 11, "arabic": "يُوسُف",      "name": "Yusuf",      "meaning": "Son of Yaqub"},
    {"number": 12, "arabic": "أَيُّوب",     "name": "Ayyub",      "meaning": "The patient one"},
    {"number": 13, "arabic": "شُعَيْب",     "name": "Shuayb",     "meaning": "Sent to people of Madyan"},
    {"number": 14, "arabic": "مُوسَى",      "name": "Musa",       "meaning": "Spoke to Allah directly"},
    {"number": 15, "arabic": "هَارُون",     "name": "Harun",      "meaning": "Brother of Musa"},
    {"number": 16, "arabic": "ذُو الْكِفْل","name": "Dhul-Kifl",  "meaning": "The patient one"},
    {"number": 17, "arabic": "دَاوُد",      "name": "Dawud",      "meaning": "Given the Zabur"},
    {"number": 18, "arabic": "سُلَيْمَان",  "name": "Sulayman",   "meaning": "Ruled over jinn and humans"},
    {"number": 19, "arabic": "إِلْيَاس",    "name": "Ilyas",      "meaning": "Called people to Allah"},
    {"number": 20, "arabic": "الْيَسَع",    "name": "Al-Yasa",    "meaning": "Successor of Ilyas"},
    {"number": 21, "arabic": "يُونُس",      "name": "Yunus",      "meaning": "The one in the whale"},
    {"number": 22, "arabic": "زَكَرِيَّا",  "name": "Zakariyya",  "meaning": "Father of Yahya"},
    {"number": 23, "arabic": "يَحْيَى",     "name": "Yahya",      "meaning": "Given wisdom as a child"},
    {"number": 24, "arabic": "عِيسَى",      "name": "Isa",        "meaning": "Born of Maryam"},
    {"number": 25, "arabic": "مُحَمَّد",    "name": "Muhammad",   "meaning": "The praised one — Final Prophet ﷺ"},
]

# ─── Names of Prophet Muhammad ﷺ ─────────────────────────────────────────────

PROPHET_MUHAMMAD_NAMES = [
    {"number": 1,  "arabic": "مُحَمَّد",         "transliteration": "Muhammad",          "meaning": "The Most Praised"},
    {"number": 2,  "arabic": "أَحْمَد",           "transliteration": "Ahmad",             "meaning": "The Most Commendable"},
    {"number": 3,  "arabic": "الْمَاحِي",         "transliteration": "Al-Mahi",           "meaning": "The Eraser of disbelief"},
    {"number": 4,  "arabic": "الْحَاشِر",         "transliteration": "Al-Hashir",         "meaning": "The Gatherer of people"},
    {"number": 5,  "arabic": "الْعَاقِب",         "transliteration": "Al-Aqib",           "meaning": "The Last of prophets"},
    {"number": 6,  "arabic": "طه",                "transliteration": "Taha",              "meaning": "Pure and Guide"},
    {"number": 7,  "arabic": "يس",                "transliteration": "Yasin",             "meaning": "O Perfect Man"},
    {"number": 8,  "arabic": "الْمُصْطَفَى",      "transliteration": "Al-Mustafa",        "meaning": "The Chosen One"},
    {"number": 9,  "arabic": "الْمُجْتَبَى",      "transliteration": "Al-Mujtaba",        "meaning": "The Selected One"},
    {"number": 10, "arabic": "الْمُرْتَضَى",      "transliteration": "Al-Murtada",        "meaning": "The Approved One"},
    {"number": 11, "arabic": "خَاتَمُ الْأَنْبِيَاء","transliteration": "Khatamul Anbiya","meaning": "Seal of the Prophets"},
    {"number": 12, "arabic": "رَسُولُ اللَّه",    "transliteration": "Rasulullah",        "meaning": "Messenger of Allah"},
    {"number": 13, "arabic": "نَبِيُّ اللَّه",    "transliteration": "Nabiyyullah",       "meaning": "Prophet of Allah"},
    {"number": 14, "arabic": "حَبِيبُ اللَّه",    "transliteration": "Habibullah",        "meaning": "Beloved of Allah"},
    {"number": 15, "arabic": "صَفِيُّ اللَّه",    "transliteration": "Safiyyullah",       "meaning": "The Pure of Allah"},
    {"number": 16, "arabic": "الصَّادِق",         "transliteration": "As-Sadiq",          "meaning": "The Truthful"},
    {"number": 17, "arabic": "الْأَمِين",         "transliteration": "Al-Amin",           "meaning": "The Trustworthy"},
    {"number": 18, "arabic": "الشَّاهِد",         "transliteration": "Ash-Shahid",        "meaning": "The Witness"},
    {"number": 19, "arabic": "الْبَشِير",         "transliteration": "Al-Bashir",         "meaning": "The Bearer of good news"},
    {"number": 20, "arabic": "النَّذِير",         "transliteration": "An-Nadhir",         "meaning": "The Warner"},
    {"number": 21, "arabic": "الدَّاعِي",         "transliteration": "Ad-Dai",            "meaning": "The Caller to Allah"},
    {"number": 22, "arabic": "النُّور",           "transliteration": "An-Nur",            "meaning": "The Light"},
    {"number": 23, "arabic": "السِّرَاج",         "transliteration": "As-Siraj",          "meaning": "The Lamp"},
    {"number": 24, "arabic": "الْهَادِي",         "transliteration": "Al-Hadi",           "meaning": "The Guide"},
    {"number": 25, "arabic": "الرَّحْمَة",        "transliteration": "Ar-Rahmah",         "meaning": "The Mercy"},
    {"number": 26, "arabic": "رَحْمَةٌ لِلْعَالَمِين","transliteration": "Rahmatullil Alamin","meaning": "Mercy to all the worlds"},
    {"number": 27, "arabic": "الشَّفِيع",         "transliteration": "Ash-Shafi",         "meaning": "The Intercessor"},
    {"number": 28, "arabic": "الْكَرِيم",         "transliteration": "Al-Karim",          "meaning": "The Noble"},
    {"number": 29, "arabic": "الْحَلِيم",         "transliteration": "Al-Halim",          "meaning": "The Forbearing"},
    {"number": 30, "arabic": "الرَّؤُوف",         "transliteration": "Ar-Rauf",           "meaning": "The Compassionate"},
    {"number": 31, "arabic": "سَيِّدُ الْمُرْسَلِين","transliteration": "Sayyidul Mursalin","meaning": "Master of all Messengers"},
    {"number": 32, "arabic": "إِمَامُ الْمُتَّقِين","transliteration": "Imamul Muttaqin", "meaning": "Leader of the pious"},
    {"number": 33, "arabic": "الْمُقَدَّس",       "transliteration": "Al-Muqaddas",       "meaning": "The Holy one"},
    {"number": 34, "arabic": "الْمُبَشِّر",       "transliteration": "Al-Mubashshir",     "meaning": "The Announcer of glad tidings"},
    {"number": 35, "arabic": "الْمُنْذِر",        "transliteration": "Al-Mundhir",        "meaning": "The Warner of punishment"},
    {"number": 36, "arabic": "الْمَهْدِي",        "transliteration": "Al-Mahdi",          "meaning": "The Guided one"},
    {"number": 37, "arabic": "الصَّابِر",         "transliteration": "As-Sabir",          "meaning": "The Patient one"},
    {"number": 38, "arabic": "الشَّاكِر",         "transliteration": "Ash-Shakir",        "meaning": "The Grateful one"},
    {"number": 39, "arabic": "الْمُتَوَكِّل",     "transliteration": "Al-Mutawakkil",     "meaning": "The one who relies on Allah"},
    {"number": 40, "arabic": "الْأَوَّل",         "transliteration": "Al-Awwal",          "meaning": "The First prophet created"},
    {"number": 41, "arabic": "الْآخِر",           "transliteration": "Al-Akhir",          "meaning": "The Last prophet sent"},
    {"number": 42, "arabic": "الْفَاتِح",         "transliteration": "Al-Fatih",          "meaning": "The Opener"},
    {"number": 43, "arabic": "الْخَاتِم",         "transliteration": "Al-Khatim",         "meaning": "The Seal"},
    {"number": 44, "arabic": "الْمَبْعُوث",       "transliteration": "Al-Mab'uth",        "meaning": "The Sent one"},
    {"number": 45, "arabic": "الْمَحْمُود",       "transliteration": "Al-Mahmud",         "meaning": "The Praised one"},
    {"number": 46, "arabic": "الْمَاجِد",         "transliteration": "Al-Majid",          "meaning": "The Glorious"},
    {"number": 47, "arabic": "الْوَلِي",          "transliteration": "Al-Wali",           "meaning": "The Friend of Allah"},
    {"number": 48, "arabic": "الصَّفِي",          "transliteration": "As-Safi",           "meaning": "The Pure"},
    {"number": 49, "arabic": "نَبِيُّ التَّوْبَة", "transliteration": "Nabiyyut Tawbah",  "meaning": "The Prophet of repentance"},
    {"number": 50, "arabic": "نَبِيُّ الرَّحْمَة", "transliteration": "Nabiyyur Rahmah",  "meaning": "The Prophet of mercy"},
]


# ─── Routes — Allah Names ─────────────────────────────────────────────────────

@names_bp.route('/allah', methods=['GET'])
@jwt_required()
def get_allah_names():
    return jsonify({
        'title': '99 Names of Allah',
        'total': len(ALLAH_NAMES),
        'names': ALLAH_NAMES
    }), 200


@names_bp.route('/allah/<int:number>', methods=['GET'])
@jwt_required()
def get_allah_name(number):
    if not (1 <= number <= 99):
        return jsonify({'error': 'Number must be between 1 and 99.'}), 400
    name = next((n for n in ALLAH_NAMES if n['number'] == number), None)
    return jsonify({'name': name}), 200


# ─── Routes — 25 Prophets ─────────────────────────────────────────────────────

@names_bp.route('/prophets', methods=['GET'])
@jwt_required()
def get_prophets():
    return jsonify({
        'title':    '25 Prophets in Islam',
        'total':    len(PROPHETS),
        'prophets': PROPHETS
    }), 200


@names_bp.route('/prophets/<int:number>', methods=['GET'])
@jwt_required()
def get_prophet(number):
    if not (1 <= number <= 25):
        return jsonify({'error': 'Number must be between 1 and 25.'}), 400
    prophet = next((p for p in PROPHETS if p['number'] == number), None)
    return jsonify({'prophet': prophet}), 200


# ─── Routes — Prophet Muhammad ﷺ Names ───────────────────────────────────────

@names_bp.route('/prophet-muhammad', methods=['GET'])
@jwt_required()
def get_prophet_muhammad_names():
    return jsonify({
        'title': 'Names and Titles of Prophet Muhammad ﷺ',
        'total': len(PROPHET_MUHAMMAD_NAMES),
        'names': PROPHET_MUHAMMAD_NAMES
    }), 200


@names_bp.route('/prophet-muhammad/<int:number>', methods=['GET'])
@jwt_required()
def get_prophet_muhammad_name(number):
    if not (1 <= number <= len(PROPHET_MUHAMMAD_NAMES)):
        return jsonify({'error': f'Number must be between 1 and {len(PROPHET_MUHAMMAD_NAMES)}.'}), 400
    name = next((n for n in PROPHET_MUHAMMAD_NAMES if n['number'] == number), None)
    return jsonify({'name': name}), 200