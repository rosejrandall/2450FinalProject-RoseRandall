import csv
from datetime import datetime, timedelta
import os

# --- Files renamed for use ---
CLIENTS_FILE = 'clients.txt'
TECHNICIANS_FILE = 'technicians.txt'
APPOINTMENTS_FILE = 'appointments.txt'

# --- Services offered and prices ---
SERVICES = {
    '1': ('Manicure', 45.00),
    '2': ('Pedicure', 45.00),
    '3': ('Gel Manicure', 55.00),
    '4': ('Gel Pedicure', 55.00)
}

# --- CORE MODEL CLASSES ---

class Client:
    """Represents a salon customer."""
    def __init__(self, name, phone, client_id):
        self.client_id = client_id
        self.name = name
        self.phone = phone

    def __str__(self):
        return f"C{self.client_id} - {self.name}"


class Technician:
    """Represents a nail technician with their schedule."""
    def __init__(self, name, tech_id):
        self.tech_id = tech_id
        self.name = name
        self.availability = {}
        self.schedule = {}

    def __str__(self):
        return f"T{self.tech_id} - {self.name}"


class Appointment:
    """Represents a booking instance."""
    def __init__(self, date, time, client, technician, appt_id, service, price, status="Booked"):
        self.appt_id = appt_id
        self.date = date
        self.time = time
        self.client = client
        self.technician = technician
        self.service = service
        self.price = float(price)
        self.status = status

    def __str__(self):
        status_info = f" | Status: {self.status}" if self.status != "Booked" else ""
        return (f"[{self.appt_id}] {self.date} @ {self.time} | Service: {self.service} (${self.price:.2f})"
                f"{status_info}\n    - Technician: {self.technician.name} | Client: {self.client.name}")


# --- BOOKING MANAGER (Controller) ---

class BookingManager:
    """Manages all data and implements business logic, including ID generation."""
    def __init__(self):
        self.clients = {}
        self.technicians = {}
        self.appointments = {}
        self._next_client_id = 101
        self._next_tech_id = 201
        self._next_appt_id = 3001
        self._load_initial_data()
        self._update_next_ids()

    def _load_clients(self):
        if not os.path.exists(CLIENTS_FILE):
            return
        with open(CLIENTS_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                client_id, name, phone = row
                self.clients[client_id] = Client(name, phone, client_id)
        print(f"SUCCESS: Loaded {len(self.clients)} clients from {CLIENTS_FILE}.")

    def _save_client(self, client: Client):
        file_exists = os.path.exists(CLIENTS_FILE) and os.path.getsize(CLIENTS_FILE) > 0
        with open(CLIENTS_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['client_id', 'name', 'phone'])
            writer.writerow([client.client_id, client.name, client.phone])

    def _load_technicians(self):
        if not os.path.exists(TECHNICIANS_FILE):
            return
        with open(TECHNICIANS_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                tech_id, name = row
                self.technicians[tech_id] = Technician(name, tech_id)
        print(f"SUCCESS: Loaded {len(self.technicians)} technicians from {TECHNICIANS_FILE}.")

    def _save_technician(self, technician: Technician):
        file_exists = os.path.exists(TECHNICIANS_FILE) and os.path.getsize(TECHNICIANS_FILE) > 0
        with open(TECHNICIANS_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['tech_id', 'name'])
            writer.writerow([technician.tech_id, technician.name])

    def _load_appointments(self):
        """Loads appointments and rebuilds technician schedules."""
        if not os.path.exists(APPOINTMENTS_FILE):
            return 0
        count = 0
        with open(APPOINTMENTS_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                (appt_id, date, time, client_id, tech_id, service, price, status) = row
                client = self.clients.get(client_id)
                tech = self.technicians.get(tech_id)
                if not all([client, tech]):
                    print(f"WARNING: Skipping Appt {appt_id}. Linked Client or Tech not found.")
                    continue
                new_appt = Appointment(date, time, client, tech, appt_id, service, price, status)
                self.appointments[appt_id] = new_appt
                count += 1
                if date not in tech.schedule:
                    tech.schedule[date] = []
                tech.schedule[date].append(new_appt)
                if status == "Booked":
                    if date in tech.availability and time in tech.availability[date]:
                        tech.availability[date].remove(time)
        print(f"SUCCESS: Loaded {count} appointments from {APPOINTMENTS_FILE}.")
        return count

    def _rewrite_appointments_file(self):
        """Rewrites the entire appointments file with the current state of appointments."""
        appointments_to_save = [appt for appt in self.appointments.values()
                                if appt.status in ["Booked", "Canceled"]]
        with open(APPOINTMENTS_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['appt_id', 'date', 'time', 'client_id', 'tech_id', 'service', 'price', 'status'])
            for appt in appointments_to_save:
                writer.writerow([
                    appt.appt_id,
                    appt.date,
                    appt.time,
                    appt.client.client_id,
                    appt.technician.tech_id,
                    appt.service,
                    f"{appt.price:.2f}",
                    appt.status
                ])

    def _update_next_ids(self):
        """Sets the next ID counters based on the maximum ID loaded from files."""
        if self.clients:
            max_client_id = max(int(cid) for cid in self.clients.keys())
            self._next_client_id = max_client_id + 1
        if self.technicians:
            max_tech_id = max(int(tid) for tid in self.technicians.keys())
            self._next_tech_id = max_tech_id + 1
        if self.appointments:
            max_appt_id = max(int(aid) for aid in self.appointments.keys())
            self._next_appt_id = max_appt_id + 1

    def _load_initial_data(self):
        """Load data from files and then apply initial availability/schedule."""
        self._load_clients()
        self._load_technicians()
        alice = next((t for t in self.technicians.values() if t.name == "Alice"), None)
        bob = next((t for t in self.technicians.values() if t.name == "Bob"), None)
        if not alice:
            alice = self.create_technician("Alice")
        if not bob:
            bob = self.create_technician("Bob")
        alice.availability = {}
        bob.availability = {}
        alice.availability['2025-11-21'] = ["10:00", "11:00", "15:00"]
        bob.availability['2025-11-21'] = ["14:00", "16:00"]
        self._load_appointments()
        if not self.clients:
            self.create_client("Cathy Smith", "555-1234")

    # --- Booking Functions ---

    def book_appointment(self, client_id, tech_id, date, time, service, price):
        """Creates an appointment if the slot is available."""
        client = self.clients.get(client_id)
        tech = self.technicians.get(tech_id)
        if not all([client, tech]):
            print("ERROR: Invalid Client or Technician ID.")
            return
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print("ERROR: Invalid date format (use YYYY-MM-DD).")
            return
        if date not in tech.availability or time not in tech.availability[date]:
            print(f"ERROR: {tech.name} is not available at {time} on {date} (already booked or not scheduled).")
            return
        new_id = self._get_next_appt_id()
        new_appt = Appointment(date, time, client, tech, new_id, service, price)
        if date not in tech.schedule:
            tech.schedule[date] = []
        tech.schedule[date].append(new_appt)
        tech.availability[date].remove(time)
        self.appointments[new_appt.appt_id] = new_appt
        self._rewrite_appointments_file()
        print("\nSUCCESS: Booking Successful!")
        print(new_appt)

    def cancel_appointment(self, appt_id):
        """Cancels an appointment and restores technician availability."""
        appt = self.appointments.get(appt_id)
        if not appt or appt.status == "Canceled":
            print(f"ERROR: Appointment ID {appt_id} not found or already canceled.")
            return
        appt.status = "Canceled"
        print(f"SUCCESS: Appointment {appt_id} canceled.")
        self._rewrite_appointments_file()
        tech = appt.technician
        date = appt.date
        time = appt.time
        if date in tech.schedule:
            tech.schedule[date] = [a for a in tech.schedule.get(date, []) if a.appt_id != appt_id]
        if date not in tech.availability:
            tech.availability[date] = []
        if time not in tech.availability[date]:
            tech.availability[date].append(time)
            tech.availability[date].sort()
            print(f"Technician {tech.name}'s slot on {date} at {time} restored.")
        else:
            print(f"Technician {tech.name}'s slot on {date} at {time} was already available (no restoration needed).")

    def find_open_slots(self, date):
        print(f"\n--- Open Slots on {date} ---")
        open_slots = []
        for tech_id, tech in self.technicians.items():
            if date in tech.availability and tech.availability[date]:
                for time in tech.availability[date]:
                    open_slots.append((tech_id, tech.name, date, time))
                    print(f"  {tech.name} (ID: T{tech_id}) at {time}")
        return open_slots

    def technician_add_slot(self, tech_id, date, time):
        tech = self.technicians.get(tech_id)
        if not tech:
            print("ERROR: Technician ID not found.")
            return
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print("ERROR: Invalid date format (use YYYY-MM-DD).")
            return
        if date not in tech.availability:
            tech.availability[date] = []
        if time in tech.availability[date]:
            print(f"ERROR: {tech.name} is already available at {time} on {date}.")
            return
        tech.availability[date].append(time)
        tech.availability[date].sort()
        print(f"SUCCESS: Slot {date} @ {time} added for {tech.name}.")

    def technician_remove_slot(self, tech_id, date, time):
        tech = self.technicians.get(tech_id)
        if not tech:
            print("ERROR: Technician ID not found.")
            return
        if date in tech.availability and time in tech.availability[date]:
            tech.availability[date].remove(time)
            if not tech.availability[date]:
                del tech.availability[date]
            print(f"SUCCESS: Slot {date} @ {time} removed for {tech.name}.")
        else:
            print(f"ERROR: Slot {date} @ {time} not found in {tech.name}'s availability.")

    def _get_next_client_id(self):
        new_id = str(self._next_client_id)
        self._next_client_id += 1
        return new_id

    def _get_next_tech_id(self):
        new_id = str(self._next_tech_id)
        self._next_tech_id += 1
        return new_id

    def _get_next_appt_id(self):
        new_id = str(self._next_appt_id)
        self._next_appt_id += 1
        return new_id

    def create_client(self, name, phone):
        new_id = self._get_next_client_id()
        new_client = Client(name, phone, new_id)
        self.clients[new_id] = new_client
        self._save_client(new_client)
        print(f"\nSUCCESS: New Client created and saved: {new_client.name} (ID: C{new_id})")
        return new_client

    def create_technician(self, name):
        new_id = self._get_next_tech_id()
        new_tech = Technician(name, new_id)
        self.technicians[new_id] = new_tech
        self._save_technician(new_tech)
        print(f"\nSUCCESS: New Technician created and saved: {new_tech.name} (ID: T{new_id})")
        return new_tech


# --- MENU INTERFACE FUNCTIONS ---

MANAGER = BookingManager()

def client_login_or_create():
    """Menu for client to log in or create a new account."""
    sub_choice = ''
    while sub_choice != '3':
        print("\n--- Client Login/Creation ---")
        print("1. Log In with Existing ID")
        print("2. Create New Client Account")
        print("3. Back to Main Menu")
        sub_choice = input("Enter choice (1-3): ").strip()
        if sub_choice == '1':
            print("Current Clients:")
            for c in MANAGER.clients.values():
                print(f"  - {c}")

            client_id = input("Enter your Client ID (e.g., 101): ").strip()
            if client_id in MANAGER.clients:
                return client_id
            else:
                print("ERROR: Invalid Client ID. Please try again.")
        elif sub_choice == '2':
            name = input("Enter your Name: ").strip()
            phone = input("Enter your Phone Number: ").strip()
            if name and phone:
                new_client = MANAGER.create_client(name, phone)
                return new_client.client_id
            else:
                print("ERROR: Name and Phone cannot be empty.")
        elif sub_choice == '3':
            return None
        else:
            print("ERROR: Invalid choice. Please enter 1, 2, or 3.")
    return None


def client_menu(client_id):
    """Client menu."""
    client = MANAGER.clients.get(client_id)
    if not client:
        return
    choice = ''
    while choice != '4':
        print(f"\n--- Welcome, {client.name} (Client Menu) ---")
        print("1. Book New Appointment")
        print("2. View My Appointments")
        print("3. Cancel Appointment")
        print("4. Back to Main Menu")
        choice = input("Enter choice (1-4): ").strip()
        if choice == '1':
            # --- SERVICE SELECTION ---
            print("\n--- Service Selection ---")
            for key, (name, price) in SERVICES.items():
                print(f"{key}. {name} (${price:.2f})")
            service_choice = input("Select a service (1-4): ").strip()
            if service_choice not in SERVICES:
                print("ERROR: Invalid service selection.")
                continue
            selected_service, selected_price = SERVICES[service_choice]
            print(f"Selected: **{selected_service}** for **${selected_price:.2f}**")
            # --- DATE/TIME/TECH SELECTION ---
            date = input("Enter date to check (YYYY-MM-DD, e.g., 2025-11-21): ").strip()
            if not date:
                print("ERROR: Date cannot be empty.")
                continue
            open_slots = MANAGER.find_open_slots(date)
            if not open_slots:
                print("No open slots found for that date.")
                continue
            tech_id = input("Enter Technician ID (e.g., 201) for booking: ").strip()
            time = input("Enter desired time (HH:MM, e.g., 10:00): ").strip()
            if tech_id and time:
                MANAGER.book_appointment(client_id, tech_id, date, time, selected_service, selected_price)
            else:
                print("ERROR: Technician ID and Time cannot be empty.")
        elif choice == '2':
            print("\n--- Your Appointments ---")
            found = False
            for appt in MANAGER.appointments.values():
                if appt.client.client_id == client_id:
                    print(appt)
                    found = True
            if not found:
                print("You have no appointments booked.")
        elif choice == '3':
            appt_id = input("Enter Appointment ID to cancel (e.g., 3001): ").strip()
            if appt_id:
                MANAGER.cancel_appointment(appt_id)
            else:
                print("ERROR: Appointment ID cannot be empty.")
        elif choice == '4':
            print("Returning to Main Menu.")
        elif choice:
            print("ERROR: Invalid choice. Please enter 1, 2, 3, or 4.")


def technician_login_or_create():
    """Menu for technician to log in or create a new account."""
    sub_choice = ''
    while sub_choice != '3':
        print("\n--- Technician Login/Creation ---")
        print("1. Log In with Existing ID")
        print("2. Create New Technician Profile")
        print("3. Back to Main Menu")
        sub_choice = input("Enter choice (1-3): ").strip()
        if sub_choice == '1':
            print("Current Technicians:")
            for t in MANAGER.technicians.values():
                print(f"  - {t}")
            tech_id = input("Enter your Technician ID (e.g., 201): ").strip()
            if tech_id in MANAGER.technicians:
                return tech_id
            else:
                print("ERROR: Invalid Technician ID. Please try again.")
        elif sub_choice == '2':
            name = input("Enter your Name: ").strip()
            if name:
                new_tech = MANAGER.create_technician(name)
                return new_tech.tech_id
            else:
                print("ERROR: Name cannot be empty.")
        elif sub_choice == '3':
            return None
        else:
            print("ERROR: Invalid choice. Please enter 1, 2, or 3.")
    return None


def technician_menu(tech_id):
    """Technician menu."""
    tech = MANAGER.technicians.get(tech_id)
    if not tech:
        return
    choice = ''
    while choice != '4':
        print(f"\n--- Welcome, {tech.name} (Technician Menu) ---")
        print("1. View My Schedule")
        print("2. Add Availability Slot")
        print("3. Remove Availability Slot")
        print("4. Back to Main Menu")
        choice = input("Enter choice (1-4): ").strip()
        if not choice:
            print("Input cannot be empty. Please enter a choice.")
            continue
        if choice == '1':
            print(f"\n--- {tech.name}'s Schedule & Availability ---")
            print("\n**Current Availability Slots (Open for Booking):**")
            if tech.availability:
                for date, times in tech.availability.items():
                    if times:
                        print(f"  {date}: {', '.join(times)}")
            else:
                print("  No future availability set.")
            print("\n**Booked/Past Appointments:**")
            found_schedule = False
            sorted_dates = sorted(tech.schedule.keys())
            for date in sorted_dates:
                appts = tech.schedule[date]
                if appts:
                    print(f"  --- {date} ---")
                    for appt in appts:
                        print(
                            f"    {appt.time} | Client: {appt.client.name} (ID: C{appt.client.client_id}) | Status: {appt.status}")
                        found_schedule = True
            if not found_schedule:
                print("No appointments currently booked.")
        elif choice == '2':
            date = input("Enter date to add (YYYY-MM-DD): ").strip()
            time = input("Enter time to add (HH:MM, e.g., 15:30): ").strip()
            if date and time:
                MANAGER.technician_add_slot(tech_id, date, time)
            else:
                print("ERROR: Date and Time cannot be empty.")
        elif choice == '3':
            date = input("Enter date to remove from (YYYY-MM-DD): ").strip()
            time = input("Enter time to remove (HH:MM): ").strip()
            if date and time:
                MANAGER.technician_remove_slot(tech_id, date, time)
            else:
                print("ERROR: Date and Time cannot be empty.")
        elif choice == '4':
            print("Returning to Main Menu.")
        elif choice:
            print("ERROR: Invalid choice. Please enter 1, 2, 3, or 4.")


def main_menu():
    """Main welcome screen."""
    print("\n" + "=" * 40)
    print("       NAIL SALON BOOKING SYSTEM ")
    print("=" * 40)
    main_choice = ''
    while main_choice != '3':
        print("\n--- Main Menu ---")
        print("1. I am a Client")
        print("2. I am a Technician")
        print("3. Exit System")
        main_choice = input("Enter your choice (1-3): ").strip()
        if not main_choice:
            print("Input cannot be empty. Please enter a choice.")
            continue
        if main_choice == '1':
            client_id = client_login_or_create()
            if client_id:
                client_menu(client_id)
        elif main_choice == '2':
            tech_id = technician_login_or_create()
            if tech_id:
                technician_menu(tech_id)
        elif main_choice == '3':
            print("\nThank you for using the Nail Salon Booking System. Goodbye!")
        else:
            print("ERROR: Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main_menu()
