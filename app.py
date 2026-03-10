from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_content():
    with open(os.path.join(BASE_DIR, 'data', 'content.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    content = load_content()
    return render_template('index.html', program=content['program'], duraklar=content['duraklar'], liderler=content['liderler'])

@app.route('/gezi')
def gezi():
    content = load_content()
    return render_template('gezi.html', duraklar=content['duraklar'])

@app.route('/duraklar')
def duraklar():
    content = load_content()
    return render_template('duraklar.html', duraklar=content['duraklar'])

@app.route('/durak/<int:durak_id>')
def durak_detay(durak_id):
    content = load_content()
    durak = next((d for d in content['duraklar'] if d['id'] == durak_id), None)
    if not durak:
        return "Durak bulunamadi", 404
    quiz = next((q for q in content['quizler']['durak_quizleri'] if q['durak_id'] == durak_id), None)
    return render_template('durak_detay.html', durak=durak, quiz=quiz, toplam_durak=len(content['duraklar']))

@app.route('/liderler')
def liderler():
    content = load_content()
    return render_template('liderler.html', liderler=content['liderler'])

@app.route('/lider/<int:lider_id>')
def lider_detay(lider_id):
    content = load_content()
    lider = next((l for l in content['liderler'] if l['id'] == lider_id), None)
    if not lider:
        return "Lider bulunamadi", 404
    return render_template('lider_detay.html', lider=lider, toplam_lider=len(content['liderler']))

@app.route('/quiz')
def quiz():
    content = load_content()
    return render_template('quiz.html', test=content['quizler']['liderlik_tarzi_testi'])

@app.route('/hap')
def hap():
    content = load_content()
    return render_template('hap.html', liderler=content['liderler'])

@app.route('/refleksiyon')
def refleksiyon():
    content = load_content()
    return render_template('refleksiyon.html', duraklar=content['duraklar'], liderler=content['liderler'])

@app.route('/profil')
def profil():
    content = load_content()
    return render_template('profil.html', duraklar=content['duraklar'], liderler=content['liderler'], sonuclar=content['quizler']['liderlik_tarzi_testi']['sonuclar'])

@app.route('/api/content')
def api_content():
    content = load_content()
    return jsonify(content)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
