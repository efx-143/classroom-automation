import requests
import webbrowser
import time
import datetime

# --- Configuration ---
CLASSROOM_ID = "E 301" # Make sure this matches the classroom you are testing
BACKEND_URL = "http://127.0.0.1:5000/api" 
CHECK_INTERVAL = 10 

# --- Main Logic ---
print(f"Classroom Client Started for: {CLASSROOM_ID}")
print(f"Checking server every {CHECK_INTERVAL} seconds...")

last_opened_link = None
last_checked_hour = None # Ghanta track karne ke liye

while True:
    try:
        now = datetime.datetime.now()
        current_hour = now.hour

        # Check if a new hour has started
        if current_hour != last_checked_hour:
            print(f"\n--- New Hour ({current_hour}:00) ---")
            last_checked_hour = current_hour
            last_opened_link = None # Reset the opened link for the new hour

        # Fetch command EVERY interval
        print(f"\nChecking server at {now.strftime('%H:%M:%S')}...")
        response = requests.get(f"{BACKEND_URL}/get-command/{CLASSROOM_ID}")
        
        if response.status_code == 200:
            data = response.json()
            action = data.get("action")
            link = data.get("link")

            if action == "open_link" and link:
                # Open link ONLY if it's different from the last opened link THIS hour
                if link != last_opened_link: 
                    print(f"  > Command received: Open Link")
                    print(f"  > Opening: {link}")
                    webbrowser.open(link) 
                    last_opened_link = link # Remember this link was opened for this hour
                else:
                    print(f"  > Link ({link}) already opened this hour. Skipping.")
            else:
                print("  > No command received or no link found for this lecture slot.")
        else:
            print(f"  > Error fetching command: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"\n  > Error connecting to server: {e}")
    except Exception as e:
        print(f"\n  > An unexpected error occurred: {e}")

    # Wait before the next check
    time.sleep(CHECK_INTERVAL)