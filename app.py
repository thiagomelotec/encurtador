from flask import Flask, request, redirect, jsonify
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
@app.route('/', methods=['GET', 'POST'])
def index():
    html = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Encurtador de Links</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f5f5f5; }
            .container { max-width: 400px; margin: 60px auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #0001; }
            input[type=url] { width: 100%; padding: 8px; margin-bottom: 10px; border-radius: 4px; border: 1px solid #ccc; }
            button { padding: 8px 16px; border: none; background: #007bff; color: #fff; border-radius: 4px; cursor: pointer; }
            .result { margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Encurtador de Links</h2>
            <form id="shortenForm">
                <input type="url" id="url" placeholder="Cole aqui a URL" required />
                <button type="submit">Encurtar</button>
            </form>
            <div class="result" id="result"></div>
        </div>
        <script>
        document.getElementById('shortenForm').onsubmit = async function(e) {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = 'Encurtando...';
            try {
                const resp = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await resp.json();
                if (resp.ok) {
                    resultDiv.innerHTML = `<b>Link curto:</b> <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
                } else {
                    resultDiv.innerHTML = `<span style='color:red'>${data.error}</span>`;
                }
            } catch (err) {
                resultDiv.innerHTML = '<span style="color:red">Erro ao conectar à API.</span>';
            }
        }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

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
