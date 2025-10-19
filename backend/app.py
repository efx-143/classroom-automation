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
    
# --- NEW: Save/Update Content Link API ---
@app.route('/api/save-content/<int:lecture_id>', methods=['POST'])
def save_content(lecture_id):
    data = request.json
    content_link = data.get('content_link')

    if content_link is None: # Check karna ki link mila ya nahi
         return jsonify({"status": "error", "message": "Content link is required"}), 400
         
    try:
        # Timetable table me content_link ko update karo specific lecture ID ke liye
        query_db(
            'UPDATE timetable SET content_link = ? WHERE id = ?',
            [content_link, lecture_id]
        )
        return jsonify({"status": "success", "message": "Content link saved!"}), 200
    except Exception as e:
        print(f"Error saving content: {e}") # Debugging ke liye error print karo
        return jsonify({"status": "error", "message": str(e)}), 500

# --- NEW: Get Command API (for Client Script) ---
# ... (get_command function waisa hi rahega) ...
# --- NEW: Get Command API (for Client Script) ---

# --- CORRECTED: Get Command API (for Client Script) ---
@app.route('/api/get-command/<classroom_id>', methods=['GET'])
def get_command(classroom_id):
    import datetime
    now = datetime.datetime.now()
    
    # Get current time in HH:MM AM/PM format (e.g., 01:33 PM)
    current_time_str = now.strftime("%I:%M %p").lstrip('0') 
    
    print(f"Checking command for {classroom_id} at {current_time_str}") # Debugging line

    try:
        # Get all non-cancelled lectures for the classroom
        lectures = query_db(
            'SELECT * FROM timetable WHERE classroom = ? AND is_cancelled = 0',
            [classroom_id]
        )

        found_lecture = None
        for lecture in lectures:
            # Extract start and end times from the 'time' string (e.g., "01:30 PM - 02:30 PM")
            try:
                time_parts = lecture['time'].split(' - ')
                start_time_str = time_parts[0]
                end_time_str = time_parts[1]

                # Convert string times to time objects for comparison
                start_time = datetime.datetime.strptime(start_time_str, '%I:%M %p').time()
                end_time = datetime.datetime.strptime(end_time_str, '%I:%M %p').time()
                current_time = now.time()

                # Check if current time is within the lecture slot
                if start_time <= current_time < end_time:
                    print(f"  > Match found: Lecture ID {lecture['id']} ({lecture['subject']}) is ongoing.") # Debugging line
                    found_lecture = lecture
                    break # Stop checking once a match is found
            except Exception as e:
                print(f"  > Error parsing time '{lecture['time']}': {e}") # Debugging line
                continue # Skip this lecture if time format is wrong

        if found_lecture and found_lecture['content_link']:
            print(f"  > Sending command: Open Link {found_lecture['content_link']}") # Debugging line
            return jsonify({
                "action": "open_link",
                "link": found_lecture['content_link']
            }), 200
        else:
            if found_lecture:
                 print("  > Lecture found, but no content link saved.") # Debugging line
            else:
                 print("  > No ongoing lecture found for this classroom.") # Debugging line
            return jsonify({"action": "none"}), 200
            
    except Exception as e:
        print(f"  > Error in get_command: {e}") # Debugging line
        return jsonify({"action": "error", "message": str(e)}), 500

# --- Server ko run karne ke liye ---
# ... (rest of the code remains the same) ...

# Server ko run karne ke liye
if __name__ == '__main__':
    # init_db() ko yahan se call karo taaki server start hote hi DB check ho jaye
    init_db() 
    app.run(debug=True, host='0.0.0.0', port=5000)