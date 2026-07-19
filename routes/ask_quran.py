from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import os
from groq import Groq

os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE']  = '1'

ask_quran_bp = Blueprint('ask_quran', __name__)

chroma_client  = None
collection     = None
embed_model    = None
groq_client    = None
is_initialized = False


def initialize():
    global chroma_client, collection, embed_model, groq_client, is_initialized

    if is_initialized:
        return True

    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'quran.pdf')
    if not os.path.exists(pdf_path):
        return False

    print("Loading embedding model...")
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    chroma_path   = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chroma_db')
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    existing = [c.name for c in chroma_client.list_collections()]

    if 'quran' in existing:
        print("Loading Quran from existing ChromaDB...")
        collection = chroma_client.get_collection('quran')
    else:
        print("Reading Quran PDF — this takes 2-3 minutes first time...")
        reader = PdfReader(pdf_path)
        chunks = []
        ids    = []
        idx    = 0

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
            text  = text.strip()
            parts = [text[i:i+500] for i in range(0, len(text), 400)]
            for part in parts:
                part = part.strip()
                if len(part) > 50:
                    chunks.append(part)
                    ids.append(f"chunk_{idx}")
                    idx += 1

        print(f"Created {len(chunks)} chunks. Generating embeddings...")
        collection = chroma_client.create_collection('quran')

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_ids    = ids[i:i+batch_size]
            embeddings   = embed_model.encode(batch_chunks).tolist()
            collection.add(
                documents=batch_chunks,
                embeddings=embeddings,
                ids=batch_ids
            )
            print(f"Processed {min(i+batch_size, len(chunks))}/{len(chunks)} chunks...")

        print("Quran stored in ChromaDB!")

    groq_client    = Groq(api_key=os.getenv('GROQ_API_KEY'))
    is_initialized = True
    print("Quran bot ready!")
    return True


@ask_quran_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    data     = request.get_json()
    question = data.get('question', '').strip()

    if not question or len(question) < 5:
        return jsonify({'error': 'Please enter a valid question.'}), 400

    ready = initialize()
    if not ready:
        return jsonify({'error': 'quran.pdf not found in project folder.'}), 500

    try:
        question_embedding = embed_model.encode([question]).tolist()[0]
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=10
        )

        context = "\n\n".join(results['documents'][0])

        prompt = f"""You are an expert Quran Assistant with deep knowledge of the Holy Quran.
Your goal is to provide accurate, respectful, and well-structured answers based on the Quran.

STRICT RULES:
- NEVER invent verses, references, or interpretations
- NEVER present anything as Quranic unless supported by the retrieved text
- ALWAYS cite Surah name and verse number when available
- ALWAYS recognize Arabic/Islamic terms:
  Jannah = Paradise, Jahannam = Hellfire, Salah = Prayer
  Zakat = Charity, Firawn = Pharaoh, Kaaba = Sacred House
  Sawm = Fasting, Hajj = Pilgrimage, Iman = Faith
  Tawbah = Repentance, Taqwa = God-consciousness
  Dunya = Worldly life, Akhirah = Hereafter
  Rasool = Messenger, Nabi = Prophet
- If asked about a Surah explain its themes, lessons and significance
- If not enough information say exactly: "I could not find a direct answer to your question in the provided Quran text."

RESPONSE FORMAT:
Answer:
[Direct clear answer in 2-3 sentences]

Evidence:
[Relevant verse or passage from the Quran text]

Explanation:
[Deeper explanation with context and lessons]

Reference:
[Surah name and verse numbers]

Retrieved Quran Text:
{context}

Question: {question}

Answer:"""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        return jsonify({
            'question': question,
            'answer':   answer,
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ask_quran_bp.route('/reload', methods=['POST'])
@jwt_required()
def reload():
    global is_initialized
    is_initialized = False
    ready = initialize()
    if ready:
        return jsonify({'message': 'Quran bot reloaded.'}), 200
    return jsonify({'error': 'Failed to reload.'}), 500