from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ваш-секретный-ключ'  # Измените на свой!

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модели данных
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    token = db.Column(db.String(32), unique=True)
    token_expiration = db.Column(db.DateTime)
    notes = db.relationship('Note', backref='author', lazy=True)

    def set_password(self, password):
        """Хеширует пароль перед сохранением"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет соответствие пароля"""
        return check_password_hash(self.password, password)

    def generate_token(self):
        """Генерирует токен для пользователя"""
        self.token = secrets.token_hex(16)
        self.token_expiration = datetime.utcnow() + timedelta(days=1)
        return self.token

    @staticmethod
    def check_token(token):
        """Проверяет валидность токена"""
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        if not token or not User.check_token(token):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    """Автоматически добавляет текущую дату во все шаблоны"""
    return {'now': datetime.now()}

# Маршруты
@app.route('/')
def index():
    return render_template('index.html', now=datetime.now())

@app.route('/home')
def home():
    """Домашняя страница с кнопками входа и регистрации"""
    return render_template('home.html')

@app.route('/view-db')
@login_required  # если нужно ограничить доступ
def view_db():
    """Страница просмотра базы данных"""
    users = User.query.all()
    notes = Note.query.all()
    return render_template('view_db.html', users=users, notes=notes, now=datetime.now())

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Проверка на существующего пользователя
        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован')
            return redirect(url_for('register'))
        
        # Создание нового пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            token = user.generate_token()
            db.session.commit()
            response = redirect(url_for('index'))
            response.set_cookie('token', token, httponly=True)
            return response
        
        flash('Неверное имя пользователя или пароль')
        return redirect(url_for('login'))
    
    return render_template('login.html', now=datetime.now())  # Добавлено now

@app.route('/logout')
def logout():
    """Выход из системы"""
    token = request.cookies.get('token')
    if token:
        user = User.query.filter_by(token=token).first()
        if user:
            user.token = None
            user.token_expiration = None
            db.session.commit()
    response = redirect(url_for('index'))
    response.set_cookie('token', '', expires=0)
    return response

@app.route('/notes')
@login_required
def notes():
    """Страница заметок (только для авторизованных)"""
    token = request.cookies.get('token')
    user = User.check_token(token)
    
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')
        if title and content:
            new_note = Note(title=title, subtitle=subtitle, content=content, author=user)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes'))
    
    # Показываем только заметки текущего пользователя
    notes = Note.query.filter_by(user_id=user.id).order_by(Note.created_at.desc()).all()
    return render_template('notes.html', notes=notes, now=datetime.now())

# Создание таблиц в БД
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)