"""
AI Powered Smart Content and Notes Generator
B.Tech Final Year Project - Computer Science
Author: [Your Name]
SDG Alignment: SDG 4 – Quality Education
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import io
import json
from functools import wraps
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import re

# ─── NEW google-genai SDK (replaces deprecated google.generativeai) ───────────
from google import genai
from google.genai import types

# ─── App Configuration ────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart-notes-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///smart_notes.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Gemini AI Setup ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = 'gemini-2.5-flash'

# ─── Database Models ──────────────────────────────────────────────────────────
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # FIX: datetime.utcnow is removed in Python 3.12+; use timezone-aware UTC now
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.relationship('Note', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    notes_content = db.Column(db.Text, nullable=False)
    summary_content = db.Column(db.Text, nullable=False)
    key_points = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_favorite = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'notes_content': self.notes_content,
            'summary_content': self.summary_content,
            'key_points': self.key_points,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p'),
            'is_favorite': self.is_favorite
        }


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ─── Auth Decorator ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ─── AI Helper Functions ──────────────────────────────────────────────────────
def generate_notes(topic):
    prompt = f"""You are an expert academic tutor and content creator. Generate comprehensive, 
    well-structured study notes for the topic: "{topic}"

    Format your response with these EXACT sections using markdown:

    ## 📚 Introduction
    [Write a clear 2-3 paragraph introduction explaining the topic]

    ## 🎯 Core Concepts
    [List and explain 4-6 main concepts with bullet points]

    ## 📖 Detailed Explanation
    [Provide an in-depth explanation covering all important aspects, 4-6 paragraphs]

    ## 🔬 Examples & Applications
    [Give 3-4 practical real-world examples]

    ## ⚡ Important Formulas / Key Definitions
    [List important formulas, definitions, or technical terms]

    ## 🔗 Related Topics
    [List 4-5 related topics to explore next]

    Make the notes educational, accurate, and suitable for B.Tech/undergraduate students.
    Use clear, concise language. Include technical depth while remaining accessible."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def generate_summary(topic, notes):
    prompt = f"""Based on this topic "{topic}" and the following notes, 
    create a concise executive summary in 150-200 words.
    
    Notes context: {notes[:500]}...
    
    The summary should:
    - Capture the essence of the topic in 3-4 sentences
    - Highlight the most critical points
    - Be written in clear, accessible language
    - End with the key takeaway
    
    Return ONLY the summary text, no headers or formatting."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


def generate_key_points(topic):
    prompt = f"""Generate exactly 6 key points/facts about "{topic}" for quick revision.
    
    Format as a JSON array of strings like:
    ["Point 1 here", "Point 2 here", "Point 3 here", "Point 4 here", "Point 5 here", "Point 6 here"]
    
    Each point should be:
    - One sentence, clear and factual
    - Important for exam/revision purposes
    - Different from each other
    
    Return ONLY the JSON array, nothing else."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = response.text.strip()
    # Clean markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    try:
        points = json.loads(text)
        return json.dumps(points)
    except:
        return json.dumps([f"Key concept about {topic}"] * 6)


def chat_with_ai(message, context=""):
    prompt = f"""You are a helpful AI study assistant for students. 
    Answer this study-related question clearly and concisely:
    
    {f'Context: The student has been studying: {context}' if context else ''}
    
    Question: {message}
    
    Provide a helpful, accurate response in 2-4 sentences. If it's a math/formula question, 
    show the steps. Keep the tone friendly and encouraging for students."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text


# ─── Page Routes ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='login')


@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='register')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    # FIX: db.session.get() replaces deprecated Model.query.get() in SQLAlchemy 2.0
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', user=user)


@app.route('/generator')
def generator():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user = db.session.get(User, session['user_id'])
    return render_template('generator.html', user=user)


@app.route('/notes')
def my_notes():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user = db.session.get(User, session['user_id'])
    return render_template('my_notes.html', user=user)


# ─── Auth API Routes ──────────────────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not all([username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': 'Account created successfully', 'username': username}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({'message': 'Login successful', 'username': user.username}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


# ─── Notes API Routes ─────────────────────────────────────────────────────────
@app.route('/api/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json()
    topic = data.get('topic', '').strip()

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    if len(topic) < 3:
        return jsonify({'error': 'Topic must be at least 3 characters'}), 400

    try:
        notes = generate_notes(topic)
        summary = generate_summary(topic, notes)
        key_points = generate_key_points(topic)

        note = Note(
            user_id=session['user_id'],
            topic=topic,
            notes_content=notes,
            summary_content=summary,
            key_points=key_points
        )
        db.session.add(note)
        db.session.commit()

        return jsonify({
            'id': note.id,
            'topic': topic,
            'notes': notes,
            'summary': summary,
            'key_points': json.loads(key_points),
            'created_at': note.created_at.strftime('%d %b %Y, %I:%M %p')
        }), 200

    except Exception as e:
        return jsonify({'error': f'AI generation failed: {str(e)}'}), 500


@app.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10

    query = Note.query.filter_by(user_id=session['user_id'])
    if search:
        query = query.filter(Note.topic.ilike(f'%{search}%'))

    notes = query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'notes': [n.to_dict() for n in notes.items],
        'total': notes.total,
        'pages': notes.pages,
        'current_page': page
    }), 200


@app.route('/api/notes/<int:note_id>', methods=['GET'])
@login_required
def get_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session['user_id']).first()
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note.to_dict()), 200


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session['user_id']).first()
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted'}), 200


@app.route('/api/notes/<int:note_id>/favorite', methods=['PUT'])
@login_required
def toggle_favorite(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session['user_id']).first()
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    note.is_favorite = not note.is_favorite
    db.session.commit()
    return jsonify({'is_favorite': note.is_favorite}), 200


@app.route('/api/dashboard-stats', methods=['GET'])
@login_required
def dashboard_stats():
    user_id = session['user_id']
    total_notes = Note.query.filter_by(user_id=user_id).count()
    favorites = Note.query.filter_by(user_id=user_id, is_favorite=True).count()
    recent = Note.query.filter_by(user_id=user_id).order_by(
        Note.created_at.desc()
    ).limit(5).all()
    now_utc = datetime.now(timezone.utc)
    today = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    this_week = Note.query.filter_by(user_id=user_id).filter(
        Note.created_at >= today
    ).count()

    return jsonify({
        'total_notes': total_notes,
        'favorites': favorites,
        'this_week': this_week,
        'recent_notes': [{'id': n.id, 'topic': n.topic,
                          'created_at': n.created_at.strftime('%d %b %Y')} for n in recent]
    }), 200


# ─── PDF Download ─────────────────────────────────────────────────────────────
@app.route('/api/notes/<int:note_id>/pdf', methods=['GET'])
@login_required
def download_pdf(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session['user_id']).first()
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
        fontSize=22, spaceAfter=6, textColor=HexColor('#1a1a2e'),
        alignment=TA_CENTER, fontName='Helvetica-Bold')

    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, spaceAfter=20, textColor=HexColor('#6c757d'),
        alignment=TA_CENTER)

    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
        fontSize=14, spaceBefore=16, spaceAfter=8,
        textColor=HexColor('#4361ee'), fontName='Helvetica-Bold')

    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=10, spaceAfter=8, leading=16,
        textColor=HexColor('#2d3748'), alignment=TA_JUSTIFY)

    summary_style = ParagraphStyle('Summary', parent=styles['Normal'],
        fontSize=10, spaceAfter=8, leading=16,
        textColor=HexColor('#2d3748'), backColor=HexColor('#f0f4ff'),
        leftIndent=12, rightIndent=12, borderPad=8)

    story.append(Paragraph(f"Study Notes: {note.topic}", title_style))
    story.append(Paragraph(
        f"Generated on {note.created_at.strftime('%B %d, %Y')} | AI Smart Notes Generator",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#4361ee')))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Summary", heading_style))
    clean_summary = note.summary_content.replace('\n', '<br/>')
    story.append(Paragraph(clean_summary, summary_style))
    story.append(Spacer(1, 0.15*inch))

    if note.key_points:
        try:
            points = json.loads(note.key_points)
            story.append(Paragraph("Key Points", heading_style))
            for i, point in enumerate(points, 1):
                story.append(Paragraph(f"<b>{i}.</b> {point}", body_style))
            story.append(Spacer(1, 0.15*inch))
        except:
            pass

    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Detailed Notes", heading_style))

    for line in note.notes_content.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.05*inch))
            continue
        if line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
        elif line.startswith('### '):
            sub_style = ParagraphStyle('Sub', parent=styles['Heading3'],
                fontSize=11, spaceBefore=8, spaceAfter=4,
                textColor=HexColor('#2d3748'), fontName='Helvetica-Bold')
            story.append(Paragraph(line[4:], sub_style))
        elif line.startswith('- ') or line.startswith('* '):
            bullet_style = ParagraphStyle('Bullet', parent=body_style,
                leftIndent=20, bulletIndent=10)
            story.append(Paragraph(f"• {line[2:]}", bullet_style))
        elif line.startswith('**') and line.endswith('**'):
            story.append(Paragraph(f"<b>{line[2:-2]}</b>", body_style))
        else:
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e2e8f0')))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
        fontSize=8, textColor=HexColor('#adb5bd'), alignment=TA_CENTER)
    story.append(Paragraph(
        "Generated by AI Smart Notes Generator | SDG 4 - Quality Education",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f"notes_{note.topic.replace(' ', '_')[:30]}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype='application/pdf')


# ─── Chat API ─────────────────────────────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    context = data.get('context', '')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        response = chat_with_ai(message, context)
        chat_msg = ChatMessage(
            user_id=session['user_id'],
            message=message,
            response=response
        )
        db.session.add(chat_msg)
        db.session.commit()
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500


# ─── App Init ─────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
