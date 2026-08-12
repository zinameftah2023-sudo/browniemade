import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'zina_a_toi_secret_key_secure_2026'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration for Orders
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'zina.meftah2023@gmail.com'
app.config['MAIL_PASSWORD'] = 'rodg dacm ahfr qsfw'

db = SQLAlchemy(app)
mail = Mail(app)

# Google OAuth Configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='493852643366-k076pe1ol46r3c2dinglhvpl1punjldh.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

translations = {
    'fr': {
        'title': 'À toi - Un voyage émotionnel en 7 bouchées',
        'subtitle': 'un voyage émotionnel en 7 bouchées',
        'products_title': 'Les 7 Étapes de l\'Amour',
        'home': 'Accueil',
        'flavors': 'Les Goûts',
        'blog': 'Réflexions',
        'account': 'Compte',
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'register': 'Inscription',
        'cart': 'Panier',
        'checkout': 'Commander et envoyer par e-mail'
    },
    'en': {
        'title': 'À toi - An emotional journey in 7 bites',
        'subtitle': 'an emotional journey in 7 bites',
        'products_title': 'The 7 Stages of Love',
        'home': 'Home',
        'flavors': 'Flavors',
        'blog': 'Reflections',
        'account': 'Account',
        'login': 'Sign In',
        'logout': 'Logout',
        'register': 'Sign Up',
        'cart': 'Cart',
        'checkout': 'Order and send via email'
    },
    'ar': {
        'title': 'إليك - رحلة عاطفية في 7 قضمات',
        'subtitle': 'رحلة عاطفية في 7 قضمات',
        'products_title': 'مراحل الحب السبع',
        'home': 'الرئيسية',
        'flavors': 'النكهات',
        'blog': 'تأملات',
        'account': 'الحساب',
        'login': 'تسجيل الدخول',
        'logout': 'تسجيل الخروج',
        'register': 'إنشاء حساب',
        'cart': 'السلة',
        'checkout': 'إرسال الطلب عبر البريد'
    }
}

@app.route('/')
def index():
    lang = session.get('lang', 'fr')
    return render_template('index.html', user=session.get('user'), t=translations.get(lang, translations['fr']), lang=lang)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['fr', 'en', 'ar']:
        session['lang'] = lang
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Inscription réussie ! Connectez-vous.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password and check_password_hash(user.password, password):
            session['user'] = user.username
            return redirect(url_for('index'))
        flash('Identifiant ou mot de passe incorrect.')
    return render_template('login.html')

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        email = user_info['email']
        user = User.query.filter_by(username=email).first()
        if not user:
            user = User(username=email, password=None)
            db.session.add(user)
            db.session.commit()
        session['user'] = email
    return redirect(url_for('index'))

@app.route('/submit_order', methods=['POST'])
def submit_order():
    data = request.json
    cart_items = data.get('items', [])
    customer_name = session.get('user', 'Client invité')

    order_details = f"Nouvelle commande À toi de : {customer_name}\n\nArticles & Lettres :\n"
    for item in cart_items:
        order_details += f"- {item['name']} ({item['price']})\n  Lettre : {item['letter']}\n\n"

    try:
        msg = Message('Nouvelle commande À toi !', sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
        msg.body = order_details
        mail.send(msg)
        return jsonify({'status': 'success', 'message': 'Commande envoyée avec succès à votre e-mail !'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)