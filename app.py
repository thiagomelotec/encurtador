from flask import Flask, request, redirect, jsonify, render_template
import sqlite3
import os
import string
import random

from flask import render_template_string
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'shortener.db')

# Criação do banco de dados
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        url TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# Página inicial com formulário
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route('/api/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL obrigatória'}), 400
    code = generate_code()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO links (code, url) VALUES (?, ?)', (code, url))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Erro ao gerar código'}), 500
    conn.close()
    return jsonify({'short_url': request.host_url + code})

@app.route('/<code>')
def redirect_code(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT url FROM links WHERE code = ?', (code,))
    row = c.fetchone()
    conn.close()
    if row:
        return redirect(row[0])
    return 'Link não encontrado', 404

if __name__ == '__main__':
    app.run(debug=True)
