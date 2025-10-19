import sqlite3
from flask import Flask, jsonify, request # request ko naya import kiya hai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_NAME = 'database.db' # Database ka naam ek variable me rakha

# --- Database Setup Function ---
def init_db():
    print("Setting up database...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        name TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        subject TEXT NOT NULL,
        time TEXT NOT NULL,
        classroom TEXT NOT NULL,
        content_link TEXT DEFAULT '',
        is_cancelled INTEGER DEFAULT 0,
        assigned_to TEXT DEFAULT '',
        type TEXT DEFAULT 'Regular',
        FOREIGN KEY (teacher_id) REFERENCES teachers (id)
    )
    ''')

    try:
        cursor.execute("INSERT INTO teachers (email, password, name) VALUES (?, ?, ?)", 
                       ('shilpa.t@example.com', 'password123', 'Shilpa Tambe'))
        print("Test teacher 'Shilpa Tambe' added to DB.")
    except sqlite3.IntegrityError:
        print("Test teacher 'Shilpa Tambe' already exists in DB.")

    conn.commit()
    conn.close()
    print("Database setup complete.")

# --- Helper Function ---
# Yeh function database se data fetch karne me aasaani karega
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Isse data dictionary jaisa milta hai
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit() # commit() ko yahan add kiya execute ke baad
    cursor.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# --- API Routes ---

@app.route('/')
def home():
    return jsonify({"message": "Hello! Backend server chal raha hai!"})

# --- NEW: Login API ---
@app.route('/api/login', methods=['POST']) # POST method, kyunki hum data bhej rahe hain
def login():
    data = request.json # Frontend se aa raha JSON data (email, password)
    email = data.get('email')
    password = data.get('password')
    
    # Database me teacher ko dhoondo
    teacher = query_db('SELECT * FROM teachers WHERE email = ?', [email], one=True)
    
    if teacher and teacher['password'] == password:
        # Teacher mil gaya aur password match ho gaya
        return jsonify({
            "status": "success",
            "message": "Login successful!",
            "teacher": {
                "id": teacher['id'],
                "name": teacher['name'],
                "email": teacher['email']
            }
        }), 200
    else:
        # Teacher nahi mila ya password galat hai
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# --- NEW: Get Schedule API ---
@app.route('/api/get-schedule', methods=['GET']) # GET method, kyunki hum data maang rahe hain
def get_schedule():
    # Abhi hum sabhi lectures fetch kar rahe hain, baadme teacher_id se filter kar sakte hain
    schedule = query_db('SELECT * FROM timetable WHERE is_cancelled = 0') # Sirf active lectures dikhao
    # schedule ek list of Rows hai, usse proper dictionary list banate hain
    lectures = [dict(row) for row in schedule]
    return jsonify(lectures), 200

# --- NEW: Add Lecture API ---
@app.route('/api/add-lecture', methods=['POST'])
def add_lecture():
    data = request.json
    try:
        query_db(
            'INSERT INTO timetable (teacher_id, subject, time, classroom, type) VALUES (?, ?, ?, ?, ?)',
            [1, data.get('subject'), data.get('time'), data.get('classroom'), data.get('type', 'Extra')] # Abhi ke liye teacher_id 1 (Shilpa Mam) hardcode kar rahe hain
        )
        return jsonify({"status": "success", "message": "Lecture added successfully!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    

# --- NEW: Get Command API (for Client Script) ---
@app.route('/api/get-command/<classroom_id>', methods=['GET'])
def get_command(classroom_id):
    # Abhi hum current time check karenge (Simple version)
    # Note: Real world me timezones aur exact minute matching ka dhyan rakhna hoga
    import datetime
    now = datetime.datetime.now()
    current_hour_ampm = now.strftime("%I:00 %p").lstrip('0') # Example: "09:00 AM"

    # Database me check karo ki is classroom me, is ghante me koi lecture hai kya?
    # (Yeh query abhi simplified hai, sirf ghante ke shuruwat ko match kar rahi hai)
    lecture = query_db(
        'SELECT * FROM timetable WHERE classroom = ? AND time LIKE ? AND is_cancelled = 0',
        [classroom_id, f"{current_hour_ampm}%"], 
        one=True
    )

    if lecture and lecture['content_link']:
        # Agar lecture hai aur link bhi hai
        return jsonify({
            "action": "open_link",
            "link": lecture['content_link']
        }), 200
    else:
        # Koi lecture nahi hai ya link nahi hai
        return jsonify({"action": "none"}), 200

# Server ko run karne ke liye
# ... (baaki code waisa hi rahega) ...

# Server ko run karne ke liye
if __name__ == '__main__':
    # init_db() ko yahan se call karo taaki server start hote hi DB check ho jaye
    init_db() 
    app.run(debug=True, host='0.0.0.0', port=5000)