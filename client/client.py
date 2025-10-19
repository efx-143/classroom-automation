import requests  # Backend se baat karne ke liye
import webbrowser  # Browser kholne ke liye
import time      # Wait karne ke liye
import datetime  # Time check karne ke liye

# --- Configuration ---
# Yeh ID har classroom computer par alag hoga. Abhi hum 'B 201' use kar rahe hain jo Shilpa Mam ke schedule me hai.
CLASSROOM_ID = "B 201" 
# Hamara backend server kahan chal raha hai
BACKEND_URL = "http://127.0.0.1:5000/api" 
# Kitni der me check karna hai (seconds me)
CHECK_INTERVAL = 10 

# --- Main Logic ---
print(f"Classroom Client Started for: {CLASSROOM_ID}")
print(f"Checking server every {CHECK_INTERVAL} seconds...")

last_opened_link = None
last_checked_hour = None

while True:
    try:
        now = datetime.datetime.now()
        current_hour = now.hour # Ghanta check karo
        
        # Har ghante sirf ek baar check karo, ya agar link pehle hi khul chuka hai toh skip karo
        if current_hour != last_checked_hour:
            print(f"\nChecking server at {now.strftime('%H:%M:%S')}...")
            last_checked_hour = current_hour # Update karo ki is ghante check ho gaya
            last_opened_link = None # Naye ghante me link reset karo

            # Backend se command fetch karo
            response = requests.get(f"{BACKEND_URL}/get-command/{CLASSROOM_ID}")
            
            if response.status_code == 200:
                data = response.json()
                action = data.get("action")
                link = data.get("link")

                if action == "open_link" and link:
                    if link != last_opened_link: # Agar yeh link pehle hi nahi khola hai
                        print(f"  > Command received: Open Link")
                        print(f"  > Opening: {link}")
                        webbrowser.open(link) # Browser me link kholo
                        last_opened_link = link # Yaad rakho ki yeh link khul gaya hai
                    else:
                        print("  > Link already opened for this hour.")
                else:
                    print("  > No command received or no link found for this hour.")
            else:
                print(f"  > Error fetching command: {response.status_code}")
        else:
             # Agar usi ghante me hai, toh har second '.' print karo taaki lage ki chal raha hai
             print(".", end="", flush=True)


    except requests.exceptions.RequestException as e:
        print(f"\n  > Error connecting to server: {e}")
    except Exception as e:
        print(f"\n  > An unexpected error occurred: {e}")

    # Agli check se pehle ruko
    time.sleep(CHECK_INTERVAL)