from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

# Dictionary to store notes
programmer_notes = {}

@app.route('/')
def index():
    return render_template('index.html', now=datetime.now())

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            programmer_notes[title] = content
            return redirect(url_for('notes'))
    return render_template('notes.html', notes=programmer_notes, now=datetime.now())


if __name__ == '__main__':
    app.run(debug=True)