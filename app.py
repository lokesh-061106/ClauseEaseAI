"""
Contract Language Simplifier - Main Flask Application
Production-ready web application for simplifying legal contracts
"""

import os
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, 
    get_jwt_identity, set_access_cookies, unset_jwt_cookies
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
app.config.from_object(get_config())

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Create database tables if they don't exist
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f'Database table creation notice: {e}')

# Create upload folder
try:
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f'Upload folder creation notice: {e}')

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
    if not user:
        session.clear()
        return redirect(url_for('login'))
    recent_requests = SimplificationRequest.query.filter_by(
        user_id=user.id
    ).order_by(SimplificationRequest.created_at.desc()).limit(10).all()
    
    stats = {
        'total_requests': user.simplification_requests.count(),
        'recent_requests': recent_requests
    }
    
    return render_template('dashboard.html', user=user, stats=stats)


@app.route('/simplify', methods=['GET', 'POST'])
def simplify():
    """Main simplification interface"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get input text
        text = request.form.get('text', '').strip()
        level = request.form.get('level', 'intermediate')
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if file.filename.endswith('.txt'):
                    text = file.read().decode('utf-8')
        
        if not text:
            flash('Please provide text to simplify', 'warning')
            return render_template('simplify.html')
        
        if len(text) < 10:
            flash('Text is too short. Please provide at least 10 characters.', 'warning')
            return render_template('simplify.html')
        
        try:
            start_time = time.time()
            
            # Initialize services
            simp_service, summ_service = get_services()
            preprocessor = get_preprocessor()
            readability_analyzer = get_readability_analyzer()
            glossary_service = get_glossary_service()
            
            # Preprocess text
            preprocessed = preprocessor.preprocess(text)
            cleaned_text = preprocessed['cleaned_text']
            
            # Calculate readability before
            readability_before = readability_analyzer.analyze(cleaned_text)
            
            # Import the new ML tools
            from src.summarizer import summarize_text_extractive
            from src.preservation_checker import check_preservation
            from src.preprocessing import preprocess_contract
            from src.simplifier import simplify_clause
            
            # Split text into clauses and process
            clauses = preprocess_contract(cleaned_text)
            if not clauses: clauses = [cleaned_text]
            
            final_simplified_clauses = []
            preservation_reports = []
            
            for original_clause in clauses:
                simplified_clause = simplify_clause(original_clause, level=level)
                report = check_preservation(original_clause, simplified_clause)
                
                # Auto Correction Loop
                if report['risk_level'] == "HIGH":
                    simplified_clause = simplify_clause(original_clause, level="Advanced")
                    report = check_preservation(original_clause, simplified_clause)
                    if report['risk_level'] == "HIGH":
                        simplified_clause = original_clause
                        report = check_preservation(original_clause, simplified_clause)

                final_simplified_clauses.append(simplified_clause)
                preservation_reports.append({
                    "original": original_clause,
                    "simplified": simplified_clause,
                    "report": report
                })
                
            simplified_text = " ".join(final_simplified_clauses)
            
            # Calculate readability after
            readability_after = readability_analyzer.analyze(simplified_text)
            
            # Generate ML Extractive Summary
            summary = summarize_text_extractive(cleaned_text, num_sentences=4)
            
            # Identify and highlight legal terms
            identified_terms = glossary_service.identify_terms(simplified_text)
            highlighted_text = glossary_service.highlight_terms(simplified_text, identified_terms)
            
            processing_time = time.time() - start_time
            
            # Save to database
            request_record = SimplificationRequest(
                user_id=session['user_id'],
                original_text=text,
                simplified_text=simplified_text,
                summary=summary,
                readability_before=readability_before['flesch_kincaid_grade'],
                readability_after=readability_after['flesch_kincaid_grade'],
                fog_index_before=readability_before['gunning_fog'],
                fog_index_after=readability_after['gunning_fog'],
                simplification_level=level,
                processing_time=processing_time
            )
            
            db.session.add(request_record)
            db.session.commit()
            
            return render_template(
                'simplify.html',
                original_text=text,
                simplified_text=simplified_text,
                highlighted_text=highlighted_text,
                summary=summary,
                readability_before=readability_before,
                readability_after=readability_after,
                identified_terms=identified_terms,
                preservation_reports=preservation_reports,
                level=level,
                processing_time=round(processing_time, 2)
            )
            
        except Exception as e:
            flash(f'Error processing text: {str(e)}', 'danger')
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return render_template('simplify.html')
    
    return render_template('simplify.html')


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
def admin():
    """Admin dashboard"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    glossary_terms = Glossary.query.all()
    recent_requests = SimplificationRequest.query.order_by(
        SimplificationRequest.created_at.desc()
    ).limit(20).all()
    
    stats = {
        'total_users': User.query.count(),
        'total_requests': SimplificationRequest.query.count(),
        'total_glossary_terms': Glossary.query.count()
    }
    
    return render_template(
        'admin.html',
        users=users,
        glossary_terms=glossary_terms,
        recent_requests=recent_requests,
        stats=stats
    )


@app.route('/admin/glossary/add', methods=['POST'])
def add_glossary_term():
    """Add new glossary term"""
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    term = request.form.get('term')
    explanation = request.form.get('explanation')
    category = request.form.get('category', '')
    
    if not term or not explanation:
        flash('Term and explanation are required', 'danger')
        return redirect(url_for('admin'))
    
    glossary_service = get_glossary_service()
    
    try:
        glossary_service.add_term(term, explanation, session['user_id'], category)
        flash(f'Term "{term}" added successfully', 'success')
    except Exception as e:
        flash(f'Error adding term: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))


@app.route('/admin/glossary/delete/<int:term_id>', methods=['POST'])
def delete_glossary_term(term_id):
    """Delete glossary term"""
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    glossary_service = get_glossary_service()
    
    if glossary_service.delete_term(term_id):
        flash('Term deleted successfully', 'success')
    else:
        flash('Term not found', 'danger')
    
    return redirect(url_for('admin'))


# ============================================================================
# API ROUTES (for future extensions)
# ============================================================================

@app.route('/api/simplify', methods=['POST'])
@jwt_required()
def api_simplify():
    """API endpoint for text simplification"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400
    
    text = data['text']
    level = data.get('level', 'intermediate')
    
    try:
        simp_service, _ = get_services()
        simplified = simp_service.simplify_text(text, level=level)
        
        return jsonify({
            'original': text,
            'simplified': simplified,
            'level': level
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('500.html'), 500


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    print("Database initialized successfully!")


@app.cli.command()
def create_admin():
    """Create admin user"""
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    user = User(username=username, email=email, is_admin=True)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    print("Starting Contract Language Simplifier...")
    print(f"Access the application at: http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
