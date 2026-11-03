import streamlit as st
import textstat
import re

st.set_page_config(page_title="Contract Simplifier", layout="wide")

st.title("­ƒôä Contract Language Simplifier")

<<<<<<< HEAD
# Import models and config
from models import db, User, SimplificationRequest, Glossary
from config import get_config

# Import services
from services.preprocessing import get_preprocessor
from services.readability import get_readability_analyzer
from services.simplification import get_simplification_service
from services.summarization import get_summarization_service
from services.glossary import get_glossary_service

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config.from_object(get_config())

# Production / Hugging Face Spaces: require shared database and secure secrets
if os.environ.get('FLASK_ENV') == 'production':
    missing = []
    if not os.environ.get('DATABASE_URL'):
        missing.append('DATABASE_URL (use a shared PostgreSQL, e.g. Neon or Supabase)')
    sk = app.config.get('SECRET_KEY') or ''
    if not sk or sk.startswith('dev-'):
        missing.append('SECRET_KEY (set a strong random value in Space secrets)')
    jk = app.config.get('JWT_SECRET_KEY') or ''
    if not jk or 'change-in-production' in jk:
        missing.append('JWT_SECRET_KEY (set a strong random value in Space secrets)')
    if missing:
        raise RuntimeError(
            'Production deployment requires these secrets to be set: ' + '; '.join(missing) +
            '. Add them in your Hugging Face Space ÔåÆ Settings ÔåÆ Repository secrets.'
        )

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# CORS: allow remote browsers (required for Hugging Face Spaces / public web access)
_cors_origins = os.environ.get('CORS_ORIGINS', '*')
_origins_list = _cors_origins.split(',') if _cors_origins != '*' else '*'
CORS(
    app,
    resources={r'/*': {'origins': _origins_list}},
    supports_credentials=(_origins_list != '*'),  # credentials only with specific origins
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE'],
)

# Ensure instance folder exists and create database tables once
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
with app.app_context():
    db.create_all()

# Create upload folder
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize services (lazy loading)
simplification_service = None
summarization_service = None


def get_services():
    """Lazy load AI services"""
    global simplification_service, summarization_service
    
    if simplification_service is None:
        simplification_service = get_simplification_service(
            app.config['SIMPLIFICATION_MODEL']
        )
    
    if summarization_service is None:
        summarization_service = get_summarization_service(
            app.config['SUMMARIZATION_MODEL']
        )
    
    return simplification_service, summarization_service


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # First user is admin
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        # Create session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        flash(f'Welcome back, {user.username}!', 'success')
        response = redirect(url_for('dashboard'))
        set_access_cookies(response, access_token)
        
        return response
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    response = redirect(url_for('login'))
    unset_jwt_cookies(response)
    flash('You have been logged out', 'info')
    return response


# ============================================================================
# MAIN APPLICATION ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    recent_requests = SimplificationRequest.query.filter_by(
        user_id=user.id
    ).order_by(SimplificationRequest.created_at.desc()).limit(10).all()
    
    stats = {
        'total_requests': user.simplification_requests.count(),
        'recent_requests': recent_requests
=======
def simplify_text(text):
    replacements = {
        "hereinafter": "from now on",
        "aforementioned": "mentioned earlier",
        "pursuant to": "under",
        "in accordance with": "according to",
        "notwithstanding": "despite",
        "shall": "must",
        "terminate": "end",
        "commence": "start",
>>>>>>> 2c3dc39751b0a3a237e162d794aa2a458c90aec2
    }

    for word, simple in replacements.items():
        text = re.sub(rf"\b{word}\b", simple, text, flags=re.IGNORECASE)

    return text


def summarize_text(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:2])


user_input = st.text_area("Enter Contract Text", height=250)

if st.button("Simplify"):

    if not user_input.strip():
        st.warning("Enter text first")
    else:
        simplified = simplify_text(user_input)
        summary = summarize_text(user_input)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Original")
            st.write(user_input)

        with col2:
            st.subheader("Simplified")
            st.write(simplified)

        st.subheader("Summary")
        st.info(summary)

        score = textstat.flesch_reading_ease(simplified)

        st.subheader("Readability Score")
        st.write(score)
