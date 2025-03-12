from flask import Flask, request, send_file, render_template, redirect, url_for, flash, jsonify
import yt_dlp
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_dino'  # Para mensagens flash

# Variável global para armazenar o progresso do download
progress_data = {
    "downloaded": 0,
    "total": 0,
    "status": "aguardando"
}

def progress_hook(d):
    global progress_data
    if d['status'] == 'downloading':
        progress_data['downloaded'] = d.get('downloaded_bytes', 0)
        progress_data['total'] = d.get('total_bytes', d.get('total_bytes_estimate', 0))
        progress_data['status'] = 'downloading'
    elif d['status'] == 'finished':
        progress_data['status'] = 'finalizado'

@app.route('/')
def index():
    # Reseta o progresso ao carregar a página
    global progress_data
    progress_data = {"downloaded": 0, "total": 0, "status": "aguardando"}
    return render_template('index.html')

@app.route('/progress')
def progress():
    return jsonify(progress_data)

@app.route('/download', methods=['POST'])
def download():
    global progress_data
    url = request.form.get('url')
    download_format = request.form.get('format')

    if not url:
        flash("Por favor, insira uma URL válida.")
        return redirect(url_for('index'))

    if download_format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [progress_hook],
            'quiet': True,
            'noplaylist': True,
        }
    elif download_format == 'mp4':
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'format': 'mp4'  # Alterado de 'preferredformat' para 'format'
            }],
            'progress_hooks': [progress_hook],
            'quiet': True,
            'noplaylist': True,
        }
    else:
        flash("Formato inválido.")
        return redirect(url_for('index'))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_id = info.get("id", "arquivo")
            ext = 'mp3' if download_format == 'mp3' else 'mp4'
            file_path = f"downloads/{file_id}.{ext}"
            
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                flash("Erro na conversão do arquivo.")
                return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erro: {str(e)}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Ativando o modo threaded para permitir chamadas simultâneas (necessário para a rota de progresso)
    app.run(debug=True, threaded=True)