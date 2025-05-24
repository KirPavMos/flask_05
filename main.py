from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

# Создаем таблицы при запуске приложения
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html', now=datetime.now())

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')
        if title and content:
            new_note = Note(title=title, subtitle=subtitle, content=content)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes'))
    
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('notes.html', notes=notes, now=datetime.now())

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Note': Note}

@app.route('/view-db')
def view_db():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('view_db.html', notes=notes, now=datetime.now())

if __name__ == '__main__':
    app.run(debug=True)