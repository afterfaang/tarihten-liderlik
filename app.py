from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timezone
import json
import os
import csv
import io

from config import Config
from models import db, User, UserVisitedDurak, UserDurakNote, UserQuizResult, UserHapAnswer, UserReflection

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Lutfen giris yapiniz.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Bu sayfaya erisim yetkiniz yok.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_content():
    with open(os.path.join(BASE_DIR, 'data', 'content.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================
# AUTH ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Hesabiniz devre disi birakilmis.', 'error')
                return render_template('login.html')
            login_user(user)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email veya sifre hatali.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ============================================
# EXISTING PAGE ROUTES (now with @login_required)
# ============================================

@app.route('/')
@login_required
def index():
    content = load_content()
    return render_template('index.html', program=content['program'], duraklar=content['duraklar'], liderler=content['liderler'])

@app.route('/gezi')
@login_required
def gezi():
    content = load_content()
    return render_template('gezi.html', duraklar=content['duraklar'])

@app.route('/duraklar')
@login_required
def duraklar():
    content = load_content()
    return render_template('duraklar.html', duraklar=content['duraklar'])

@app.route('/durak/<int:durak_id>')
@login_required
def durak_detay(durak_id):
    content = load_content()
    durak = next((d for d in content['duraklar'] if d['id'] == durak_id), None)
    if not durak:
        return "Durak bulunamadi", 404
    quiz = next((q for q in content['quizler']['durak_quizleri'] if q['durak_id'] == durak_id), None)
    return render_template('durak_detay.html', durak=durak, quiz=quiz, toplam_durak=len(content['duraklar']))

@app.route('/liderler')
@login_required
def liderler():
    content = load_content()
    return render_template('liderler.html', liderler=content['liderler'])

@app.route('/lider/<int:lider_id>')
@login_required
def lider_detay(lider_id):
    content = load_content()
    lider = next((l for l in content['liderler'] if l['id'] == lider_id), None)
    if not lider:
        return "Lider bulunamadi", 404
    return render_template('lider_detay.html', lider=lider, toplam_lider=len(content['liderler']))

@app.route('/quiz')
@login_required
def quiz():
    content = load_content()
    return render_template('quiz.html', test=content['quizler']['liderlik_tarzi_testi'])

@app.route('/hap')
@login_required
def hap():
    content = load_content()
    return render_template('hap.html', liderler=content['liderler'])

@app.route('/refleksiyon')
@login_required
def refleksiyon():
    content = load_content()
    return render_template('refleksiyon.html', duraklar=content['duraklar'], liderler=content['liderler'])

@app.route('/profil')
@login_required
def profil():
    content = load_content()
    return render_template('profil.html', duraklar=content['duraklar'], liderler=content['liderler'], sonuclar=content['quizler']['liderlik_tarzi_testi']['sonuclar'])

@app.route('/api/content')
@login_required
def api_content():
    content = load_content()
    return jsonify(content)


# ============================================
# DATA API ROUTES (replace localStorage)
# ============================================

@app.route('/api/user/progress')
@login_required
def api_user_progress():
    uid = current_user.id

    visited = [v.durak_id for v in UserVisitedDurak.query.filter_by(user_id=uid).all()]

    notes_rows = UserDurakNote.query.filter_by(user_id=uid).all()
    durak_notes = {str(n.durak_id): n.note_text for n in notes_rows}

    quiz_row = UserQuizResult.query.filter_by(user_id=uid).order_by(UserQuizResult.taken_at.desc()).first()
    quiz_result = None
    if quiz_row:
        quiz_result = {
            'result': quiz_row.result_key,
            'liderId': quiz_row.lider_id,
            'scores': json.loads(quiz_row.scores_json),
            'date': quiz_row.taken_at.isoformat()
        }

    hap_rows = UserHapAnswer.query.filter_by(user_id=uid).all()
    hap_answers = {}
    for h in hap_rows:
        lid = str(h.lider_id)
        if lid not in hap_answers:
            hap_answers[lid] = []
        while len(hap_answers[lid]) <= h.question_index:
            hap_answers[lid].append('')
        hap_answers[lid][h.question_index] = h.answer_text

    ref_rows = UserReflection.query.filter_by(user_id=uid).order_by(UserReflection.created_at.desc()).all()
    reflections = [{
        'id': r.id,
        'title': r.title,
        'content': r.content,
        'tag': r.tag,
        'date': r.created_at.strftime('%d %B %Y, %H:%M') if r.created_at else ''
    } for r in ref_rows]

    return jsonify({
        'visited_duraklar': visited,
        'durak_notes': durak_notes,
        'quiz_result': quiz_result,
        'hap_answers': hap_answers,
        'reflections': reflections,
        'user_name': current_user.name
    })


@app.route('/api/durak/visit', methods=['POST'])
@login_required
def api_durak_visit():
    data = request.get_json()
    durak_id = data.get('durak_id')
    if not durak_id or durak_id < 1 or durak_id > 7:
        return jsonify({'error': 'Gecersiz durak_id'}), 400

    existing = UserVisitedDurak.query.filter_by(user_id=current_user.id, durak_id=durak_id).first()
    if not existing:
        db.session.add(UserVisitedDurak(user_id=current_user.id, durak_id=durak_id))
        db.session.commit()

    visited = [v.durak_id for v in UserVisitedDurak.query.filter_by(user_id=current_user.id).all()]
    return jsonify({'visited_duraklar': visited})


@app.route('/api/durak/note', methods=['POST'])
@login_required
def api_durak_note():
    data = request.get_json()
    durak_id = data.get('durak_id')
    note = data.get('note', '').strip()
    if not durak_id:
        return jsonify({'error': 'Gecersiz durak_id'}), 400

    existing = UserDurakNote.query.filter_by(user_id=current_user.id, durak_id=durak_id).first()
    if existing:
        existing.note_text = note
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.session.add(UserDurakNote(user_id=current_user.id, durak_id=durak_id, note_text=note))
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/quiz/result', methods=['POST'])
@login_required
def api_quiz_result():
    data = request.get_json()
    result_key = data.get('result')
    lider_id = data.get('liderId')
    scores = data.get('scores', {})

    if not result_key or not lider_id:
        return jsonify({'error': 'Eksik veri'}), 400

    db.session.add(UserQuizResult(
        user_id=current_user.id,
        result_key=result_key,
        lider_id=lider_id,
        scores_json=json.dumps(scores)
    ))
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/hap/save', methods=['POST'])
@login_required
def api_hap_save():
    data = request.get_json()
    lider_id = data.get('lider_id')
    answers = data.get('answers', [])

    if not lider_id:
        return jsonify({'error': 'Gecersiz lider_id'}), 400

    for idx, answer_text in enumerate(answers):
        if not answer_text or not answer_text.strip():
            continue
        existing = UserHapAnswer.query.filter_by(
            user_id=current_user.id, lider_id=lider_id, question_index=idx
        ).first()
        if existing:
            existing.answer_text = answer_text.strip()
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.session.add(UserHapAnswer(
                user_id=current_user.id, lider_id=lider_id,
                question_index=idx, answer_text=answer_text.strip()
            ))
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/reflection/save', methods=['POST'])
@login_required
def api_reflection_save():
    data = request.get_json()
    title = data.get('title', '').strip() or 'Basliksiz Not'
    content = data.get('content', '').strip()
    tag = data.get('tag', 'genel')

    if not content:
        return jsonify({'error': 'Icerik bos olamaz'}), 400

    ref = UserReflection(user_id=current_user.id, title=title, content=content, tag=tag)
    db.session.add(ref)
    db.session.commit()

    return jsonify({
        'id': ref.id,
        'title': ref.title,
        'content': ref.content,
        'tag': ref.tag,
        'date': ref.created_at.strftime('%d %B %Y, %H:%M') if ref.created_at else ''
    })


@app.route('/api/reflection/<int:ref_id>', methods=['DELETE'])
@login_required
def api_reflection_delete(ref_id):
    ref = UserReflection.query.filter_by(id=ref_id, user_id=current_user.id).first()
    if not ref:
        return jsonify({'error': 'Not bulunamadi'}), 404
    db.session.delete(ref)
    db.session.commit()
    return jsonify({'ok': True})


# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin/')
@admin_required
def admin_dashboard():
    total_users = User.query.filter_by(is_admin=False).count()
    total_quiz = UserQuizResult.query.distinct(UserQuizResult.user_id).count()
    total_reflections = UserReflection.query.count()

    # Average visited duraks
    from sqlalchemy import func
    avg_visited = db.session.query(func.count(UserVisitedDurak.id)).group_by(UserVisitedDurak.user_id).all()
    avg_durak = round(sum(c[0] for c in avg_visited) / len(avg_visited), 1) if avg_visited else 0

    # Most common quiz result
    popular_result = db.session.query(
        UserQuizResult.result_key, func.count(UserQuizResult.id)
    ).group_by(UserQuizResult.result_key).order_by(func.count(UserQuizResult.id).desc()).first()

    # Recent logins
    recent_logins = User.query.filter(User.last_login.isnot(None)).order_by(User.last_login.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_quiz=total_quiz,
        total_reflections=total_reflections,
        avg_durak=avg_durak,
        popular_result=popular_result[0] if popular_result else '-',
        recent_logins=recent_logins
    )


@app.route('/admin/users')
@admin_required
def admin_users():
    from sqlalchemy import func

    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()

    user_data = []
    for u in users:
        visited_count = UserVisitedDurak.query.filter_by(user_id=u.id).count()
        quiz_done = UserQuizResult.query.filter_by(user_id=u.id).first() is not None
        ref_count = UserReflection.query.filter_by(user_id=u.id).count()
        hap_count = UserHapAnswer.query.filter_by(user_id=u.id).count()

        user_data.append({
            'user': u,
            'visited': visited_count,
            'quiz_done': quiz_done,
            'reflections': ref_count,
            'hap': hap_count
        })

    return render_template('admin/users.html', user_data=user_data)


@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Kullanici bulunamadi.', 'error')
        return redirect(url_for('admin_users'))

    content = load_content()
    visited = [v.durak_id for v in UserVisitedDurak.query.filter_by(user_id=user_id).all()]
    durak_notes = {str(n.durak_id): n.note_text for n in UserDurakNote.query.filter_by(user_id=user_id).all()}

    quiz_row = UserQuizResult.query.filter_by(user_id=user_id).order_by(UserQuizResult.taken_at.desc()).first()
    quiz_result = None
    if quiz_row:
        quiz_result = {
            'result': quiz_row.result_key,
            'liderId': quiz_row.lider_id,
            'scores': json.loads(quiz_row.scores_json),
            'date': quiz_row.taken_at.strftime('%d %B %Y, %H:%M')
        }

    hap_rows = UserHapAnswer.query.filter_by(user_id=user_id).order_by(UserHapAnswer.lider_id, UserHapAnswer.question_index).all()
    hap_answers = {}
    for h in hap_rows:
        lid = h.lider_id
        if lid not in hap_answers:
            hap_answers[lid] = []
        hap_answers[lid].append(h.answer_text)

    reflections = UserReflection.query.filter_by(user_id=user_id).order_by(UserReflection.created_at.desc()).all()

    return render_template('admin/user_detail.html',
        user=user, visited=visited, durak_notes=durak_notes,
        quiz_result=quiz_result, hap_answers=hap_answers,
        reflections=reflections, duraklar=content['duraklar'],
        liderler=content['liderler']
    )


@app.route('/admin/create-user', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Tum alanlar zorunludur.', 'error')
            return render_template('admin/create_user.html')

        if User.query.filter_by(email=email).first():
            flash('Bu email zaten kayitli.', 'error')
            return render_template('admin/create_user.html')

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(user)
        db.session.commit()
        flash(f'{name} basariyla olusturuldu.', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/create_user.html')


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash('Kendinizi silemezsiniz.', 'error')
        return redirect(url_for('admin_users'))

    user = db.session.get(User, user_id)
    if not user:
        flash('Kullanici bulunamadi.', 'error')
        return redirect(url_for('admin_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'{user.name} silindi.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/export')
@admin_required
def admin_export():
    from sqlalchemy import func

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ad', 'Email', 'Durak Ilerleme', 'Quiz Durumu', 'Quiz Sonucu', 'Refleksiyon Sayisi', 'HAP Cevap Sayisi', 'Kayit Tarihi', 'Son Giris'])

    users = User.query.filter_by(is_admin=False).all()
    for u in users:
        visited_count = UserVisitedDurak.query.filter_by(user_id=u.id).count()
        quiz = UserQuizResult.query.filter_by(user_id=u.id).order_by(UserQuizResult.taken_at.desc()).first()
        ref_count = UserReflection.query.filter_by(user_id=u.id).count()
        hap_count = UserHapAnswer.query.filter_by(user_id=u.id).count()

        writer.writerow([
            u.name,
            u.email,
            f'{visited_count}/7',
            'Evet' if quiz else 'Hayir',
            quiz.result_key if quiz else '-',
            ref_count,
            hap_count,
            u.created_at.strftime('%d.%m.%Y') if u.created_at else '-',
            u.last_login.strftime('%d.%m.%Y %H:%M') if u.last_login else '-'
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=kullanicilar.csv'}
    )


# ============================================
# DB INIT HELPER
# ============================================

with app.app_context():
    db.create_all()
    # Auto-create admin if not exists
    admin_email = 'admin@tarihtenliderllik.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            email=admin_email,
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
            name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f'Admin olusturuldu: {admin_email}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
