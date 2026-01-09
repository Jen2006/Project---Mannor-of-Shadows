# =============================================================================
# MANOR OF SHADOW - COMPLETE GAME WITH AUTHENTICATION & SAVE SYSTEM
# =============================================================================

from flask import Flask, render_template, request, session, redirect, url_for, g, flash, jsonify
import sqlite3
import datetime
import os
import random
import hashlib
import secrets
import json

# =============================================================================
# FLASK APPLICATION INITIALIZATION
# =============================================================================

app = Flask(__name__)
app.secret_key = 'manor_of_shadow_secret_key_2024_enhanced'
DATABASE = 'manor_of_shadow.db'

# =============================================================================
# PUZZLE CONFIGURATIONS
# =============================================================================

WORKSHOP_PARTS = {
    'G': 'Gear Mechanism',
    'S': 'Spring Coil', 
    'P': 'Piston Rod',
    'V': 'Valve Controller',
    'C': 'Circuit Board'
}
WORKSHOP_SEQUENCE = ['S', 'G', 'P', 'V', 'C']

OBSERVATORY_RIDDLE = {
    'question': 'I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?',
    'answer': 'echo'
}

LABORATORY_PATTERNS = [
    {'sequence': [2, 4, 8, 16, '?'], 'answer': '32', 'hint': 'Each number doubles the previous'},
    {'sequence': [1, 1, 2, 3, 5, '?'], 'answer': '8', 'hint': 'Each number is the sum of the two before it'},
    {'sequence': [3, 9, 27, 81, '?'], 'answer': '243', 'hint': 'Each number multiplies by 3'}
]

CONTROL_CLUES = [
    "The Red System technician isn't Alex",
    "The Blue System belongs to the Electrician", 
    "The Plumber doesn't have the Green System",
    "Sam is the Mechanic",
    "The Green System owner is the Mechanic"
]

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                player_name TEXT NOT NULL,
                user_id INTEGER,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_time TEXT,
                room1_complete BOOLEAN DEFAULT 0,
                room2_complete BOOLEAN DEFAULT 0,
                room3_complete BOOLEAN DEFAULT 0,
                final_complete BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Puzzle attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS puzzle_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                user_id INTEGER,
                room_name TEXT NOT NULL,
                attempt TEXT NOT NULL,
                is_correct BOOLEAN DEFAULT 0,
                attempted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        ''')
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                display_name TEXT,
                avatar_url TEXT,
                bio TEXT,
                preferences TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Saved games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                save_name TEXT NOT NULL,
                session_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                current_room TEXT NOT NULL,
                game_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        db.commit()

# =============================================================================
# AUTHENTICATION SYSTEM
# =============================================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def create_user(username, password, email=None):
    db = get_db()
    cursor = db.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, email, datetime.datetime.now().isoformat()))
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO user_profiles (user_id, display_name)
            VALUES (?, ?)
        ''', (user_id, username))
        
        db.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None

def authenticate_user(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user and verify_password(user['password_hash'], password):
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.datetime.now().isoformat(), user['id']))
        db.commit()
        return user
    return None

def get_user_profile(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT u.username, u.email, u.created_at, u.last_login,
               p.display_name, p.avatar_url, p.bio
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    ''', (user_id,))
    return cursor.fetchone()

# =============================================================================
# SAVE/LOAD SYSTEM
# =============================================================================

def save_game(user_id, save_name, session_id, player_name, current_room, game_data):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT id FROM saved_games 
        WHERE user_id = ? AND save_name = ? AND is_active = 1
    ''', (user_id, save_name))
    existing_save = cursor.fetchone()
    
    if existing_save:
        cursor.execute('''
            UPDATE saved_games 
            SET session_id = ?, player_name = ?, current_room = ?, 
                game_data = ?, last_updated = ?
            WHERE id = ?
        ''', (session_id, player_name, current_room, game_data, 
              datetime.datetime.now().isoformat(), existing_save['id']))
    else:
        cursor.execute('''
            INSERT INTO saved_games 
            (user_id, save_name, session_id, player_name, current_room, game_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, save_name, session_id, player_name, current_room, game_data))
    
    db.commit()
    return True

def load_game(user_id, save_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM saved_games 
        WHERE id = ? AND user_id = ? AND is_active = 1
    ''', (save_id, user_id))
    return cursor.fetchone()

def get_user_saves(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, save_name, current_room, created_at, last_updated
        FROM saved_games 
        WHERE user_id = ? AND is_active = 1
        ORDER BY last_updated DESC
    ''', (user_id,))
    return cursor.fetchall()

def delete_save(user_id, save_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE saved_games 
        SET is_active = 0 
        WHERE id = ? AND user_id = ?
    ''', (save_id, user_id))
    db.commit()
    return cursor.rowcount > 0

def get_game_state(session_id):
    progress = get_player_progress(session_id)
    if not progress:
        return None
    
    game_state = {
        'room1_complete': bool(progress['room1_complete']),
        'room2_complete': bool(progress['room2_complete']),
        'room3_complete': bool(progress['room3_complete']),
        'final_complete': bool(progress['final_complete']),
        'start_time': progress['start_time'],
        'current_room': determine_current_room(progress)
    }
    return json.dumps(game_state)

def determine_current_room(progress):
    if not progress['room1_complete']:
        return 'room1'
    elif not progress['room2_complete']:
        return 'room2'
    elif not progress['room3_complete']:
        return 'room3'
    elif not progress['final_complete']:
        return 'final'
    else:
        return 'completed'

def restore_game_state(session_id, game_data):
    data = json.loads(game_data)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE players 
        SET room1_complete = ?, room2_complete = ?, room3_complete = ?, 
            final_complete = ?, start_time = ?
        WHERE session_id = ?
    ''', (data['room1_complete'], data['room2_complete'], 
          data['room3_complete'], data['final_complete'],
          data['start_time'], session_id))
    
    db.commit()

# =============================================================================
# GAME PROGRESS FUNCTIONS
# =============================================================================

def create_player_session(session_id, player_name, user_id=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO players (session_id, player_name, user_id, start_time)
        VALUES (?, ?, ?, ?)
    ''', (session_id, player_name, user_id, datetime.datetime.now().isoformat()))
    db.commit()

def update_player_progress(session_id, room=None, completed=False):
    db = get_db()
    cursor = db.cursor()
    if room and completed:
        cursor.execute(f'UPDATE players SET {room}_complete = 1 WHERE session_id = ?', (session_id,))
    db.commit()

def get_player_progress(session_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM players WHERE session_id = ?', (session_id,))
    return cursor.fetchone()

def log_puzzle_attempt(session_id, player_name, user_id, room_name, attempt, is_correct):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO puzzle_attempts (session_id, player_name, user_id, room_name, attempt, is_correct)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, player_name, user_id, room_name, attempt, 1 if is_correct else 0))
    db.commit()

def complete_player_game(session_id, total_time):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE players 
        SET end_time = ?, total_time = ?, final_complete = 1
        WHERE session_id = ?
    ''', (datetime.datetime.now().isoformat(), total_time, session_id))
    db.commit()

def get_leaderboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT player_name, total_time, start_time, end_time
        FROM players 
        WHERE final_complete = 1 
        ORDER BY total_time ASC
        LIMIT 20
    ''')
    return cursor.fetchall()

def get_all_players():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT player_name, start_time, end_time, total_time,
               room1_complete, room2_complete, room3_complete, final_complete
        FROM players 
        ORDER BY start_time DESC
    ''')
    return cursor.fetchall()

# =============================================================================
# PUZZLE VALIDATION FUNCTIONS
# =============================================================================

def validate_workshop_puzzle(selected_sequence):
    return selected_sequence == WORKSHOP_SEQUENCE

def validate_observatory_puzzle(answer):
    return answer.lower().strip() == OBSERVATORY_RIDDLE['answer']

def validate_laboratory_puzzle(pattern_index, user_answer):
    if 0 <= pattern_index < len(LABORATORY_PATTERNS):
        return user_answer.strip() == LABORATORY_PATTERNS[pattern_index]['answer']
    return False

def validate_control_puzzle(answers):
    correct_answers = {
        'red_system': 'plumber',
        'blue_system': 'electrician', 
        'green_system': 'mechanic',
        'alex_role': 'electrician',
        'sam_role': 'mechanic',
        'taylor_role': 'plumber'
    }
    
    for key, value in correct_answers.items():
        if answers.get(key, '').lower().strip() != value:
            return False
    return True

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register.html')
        
        user_id = create_user(username, password, email)
        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists', 'error')
    
    return render_template('auth/register.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['logged_in'] = True
            flash(f'Welcome back, {username}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/auth/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('login'))
    
    user_profile = get_user_profile(session['user_id'])
    return render_template('profile.html', profile=user_profile)

# =============================================================================
# SAVE/LOAD ROUTES
# =============================================================================

@app.route('/save_game', methods=['POST'])
def save_current_game():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to save games'})
    
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'No active game session'})
    
    save_name = request.json.get('save_name', f"Save_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    game_data = get_game_state(session['session_id'])
    if not game_data:
        return jsonify({'success': False, 'message': 'No game progress to save'})
    
    success = save_game(
        session['user_id'],
        save_name,
        session['session_id'],
        session['player_name'],
        determine_current_room(get_player_progress(session['session_id'])),
        game_data
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Game saved successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to save game'})

@app.route('/load_game/<int:save_id>')
def load_saved_game(save_id):
    if 'user_id' not in session:
        flash('Please log in to load saved games', 'error')
        return redirect(url_for('login'))
    
    saved_game = load_game(session['user_id'], save_id)
    if not saved_game:
        flash('Saved game not found', 'error')
        return redirect(url_for('saves'))
    
    session['session_id'] = saved_game['session_id']
    session['player_name'] = saved_game['player_name']
    
    restore_game_state(saved_game['session_id'], saved_game['game_data'])
    
    room_endpoint_map = {
        'room1': 'room1',
        'room2': 'room2', 
        'room3': 'room3',
        'final': 'final_room',  # This fixes the issue
        'completed': 'success'
    }
    
    endpoint = room_endpoint_map.get(saved_game['current_room'], 'index')
    flash(f'Game "{saved_game["save_name"]}" loaded successfully!', 'success')
    return redirect(url_for(endpoint))

    #flash(f'Game "{saved_game["save_name"]}" loaded successfully!', 'success')
   # return redirect(url_for(saved_game['current_room']))

@app.route('/saves')
def saves():
    if 'user_id' not in session:
        flash('Please log in to view saved games', 'error')
        return redirect(url_for('login'))
    
    saved_games = get_user_saves(session['user_id'])
    return render_template('saves.html', saved_games=saved_games)

@app.route('/delete_save/<int:save_id>', methods=['POST'])
def delete_saved_game(save_id):
    if 'user_id' not in session:
        flash('Please log in to delete saved games', 'error')
        return redirect(url_for('login'))
    
    success = delete_save(session['user_id'], save_id)
    if success:
        flash('Save deleted successfully!', 'success')
    else:
        flash('Failed to delete save', 'error')
    
    return redirect(url_for('saves'))

@app.route('/quick_save')
def quick_save():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to save'})
    
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'No active game'})
    
    save_name = f"QuickSave_{datetime.datetime.now().strftime('%H:%M')}"
    game_data = get_game_state(session['session_id'])
    
    if not game_data:
        return jsonify({'success': False, 'message': 'No progress to save'})
    
    success = save_game(
        session['user_id'],
        save_name,
        session['session_id'],
        session['player_name'],
        determine_current_room(get_player_progress(session['session_id'])),
        game_data
    )
    
    return jsonify({'success': success, 'message': 'Quick save completed!' if success else 'Save failed'})

# =============================================================================
# MAIN GAME ROUTES
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to start a game', 'error')
            return redirect(url_for('login'))
        
        player_name = request.form.get('player_name', '').strip()
        if player_name:
            session['session_id'] = secrets.token_hex(16)
            session['player_name'] = player_name
            create_player_session(session['session_id'], player_name, session.get('user_id'))
            return redirect(url_for('room1'))
    
    leaderboard = get_leaderboard()
    all_players = get_all_players()
    return render_template('index.html', 
                         leaderboard=leaderboard, 
                         all_players=all_players,
                         logged_in=session.get('logged_in'),
                         username=session.get('username'))

@app.route('/room1', methods=['GET', 'POST'])
def room1():
    if 'user_id' not in session:
        flash('Please log in to play', 'error')
        return redirect(url_for('login'))
    
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        selected_sequence = request.form.getlist('part_seq')
        
        is_correct = validate_workshop_puzzle(selected_sequence)
        log_puzzle_attempt(session['session_id'], session['player_name'], 
                          session.get('user_id'), 'room1', str(selected_sequence), is_correct)
        
        if is_correct:
            update_player_progress(session['session_id'], 'room1', True)
            return redirect(url_for('room2'))
        else:
            return render_template('room1.html', 
                                 parts=WORKSHOP_PARTS,
                                 error="Incorrect assembly sequence! Check the blueprint carefully.")
    
    return render_template('room1.html', parts=WORKSHOP_PARTS)

@app.route('/room2', methods=['GET', 'POST'])
def room2():
    if 'user_id' not in session:
        flash('Please log in to play', 'error')
        return redirect(url_for('login'))
    
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    progress = get_player_progress(session['session_id'])
    if not progress or not progress['room1_complete']:
        return redirect(url_for('room1'))
    
    if request.method == 'POST':
        answer = request.form.get('riddle_answer', '')
        is_correct = validate_observatory_puzzle(answer)
        
        log_puzzle_attempt(session['session_id'], session['player_name'], 
                          session.get('user_id'), 'room2', answer, is_correct)
        
        if is_correct:
            update_player_progress(session['session_id'], 'room2', True)
            return redirect(url_for('room3'))
        else:
            return render_template('room2.html', 
                                 riddle=OBSERVATORY_RIDDLE['question'],
                                 error="Wrong answer! Think about what repeats your words in empty spaces.")
    
    return render_template('room2.html', riddle=OBSERVATORY_RIDDLE['question'])

@app.route('/room3', methods=['GET', 'POST'])
def room3():
    if 'user_id' not in session:
        flash('Please log in to play', 'error')
        return redirect(url_for('login'))
    
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    progress = get_player_progress(session['session_id'])
    if not progress or not progress['room2_complete']:
        return redirect(url_for('room2'))
    
    if 'pattern_index' not in session:
        session['pattern_index'] = random.randint(0, len(LABORATORY_PATTERNS) - 1)
    
    pattern = LABORATORY_PATTERNS[session['pattern_index']]
    
    if request.method == 'POST':
        user_answer = request.form.get('pattern_answer', '')
        is_correct = validate_laboratory_puzzle(session['pattern_index'], user_answer)
        
        log_puzzle_attempt(session['session_id'], session['player_name'], 
                          session.get('user_id'), 'room3', user_answer, is_correct)
        
        if is_correct:
            update_player_progress(session['session_id'], 'room3', True)
            session.pop('pattern_index', None)
            return redirect(url_for('final_room'))
        else:
            return render_template('room3.html', 
                                 pattern=pattern,
                                 error="Wrong pattern! Look for the mathematical relationship.")
    
    return render_template('room3.html', pattern=pattern)

@app.route('/final', methods=['GET', 'POST'])
def final_room():
    if 'user_id' not in session:
        flash('Please log in to play', 'error')
        return redirect(url_for('login'))
    
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    progress = get_player_progress(session['session_id'])
    if not progress or not progress['room3_complete']:
        return redirect(url_for('room3'))
    
    if request.method == 'POST':
        answers = {
            'red_system': request.form.get('red_system', ''),
            'blue_system': request.form.get('blue_system', ''),
            'green_system': request.form.get('green_system', ''),
            'alex_role': request.form.get('alex_role', ''),
            'sam_role': request.form.get('sam_role', ''),
            'taylor_role': request.form.get('taylor_role', '')
        }
        
        is_correct = validate_control_puzzle(answers)
        log_puzzle_attempt(session['session_id'], session['player_name'], 
                          session.get('user_id'), 'final', str(answers), is_correct)
        
        if is_correct:
            start_time = datetime.datetime.fromisoformat(progress['start_time'])
            end_time = datetime.datetime.now()
            total_time = str(end_time - start_time).split('.')[0]
            
            complete_player_game(session['session_id'], total_time)
            return redirect(url_for('success'))
        else:
            return render_template('final.html', 
                                 clues=CONTROL_CLUES,
                                 error="Incorrect solution! Use all clues systematically.")
    
    return render_template('final.html', clues=CONTROL_CLUES)

@app.route('/success')
def success():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    progress = get_player_progress(session['session_id'])
    if not progress or not progress['final_complete']:
        return redirect(url_for('index'))
    
    leaderboard = get_leaderboard()
    return render_template('success.html', 
                         escape_time=progress['total_time'],
                         player_name=session.get('player_name', 'Player'),
                         leaderboard=leaderboard)

@app.route('/leaderboard')
def leaderboard():
    leaderboard = get_leaderboard()
    all_players = get_all_players()
    return render_template('leaderboard.html', leaderboard=leaderboard, all_players=all_players)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
        print("Database initialized successfully!")
    app.run(debug=True)