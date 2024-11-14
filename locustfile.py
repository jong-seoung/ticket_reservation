from locust import HttpUser, TaskSet, task, between
import threading
import random
import string

event_id = None
category_id = None

class UserBehavior(TaskSet):
    lock = threading.Lock()  
    def on_start(self):
        name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = "password"
        email = f"{name}@example.com"
        
        phone_number = f"010{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        birth_year = random.randint(1980, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  
        birthday = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"

        signup_data = {
            "name": name,
            "password": password,
            "email": email,
            "phone_number": phone_number,
            "birthday": birthday
        }
        
        response = self.client.post("/accounts/register/", json=signup_data)
        
        if response.status_code == 201:
            self.login(email, password)

            if self.lock.acquire(blocking=False):  
                self.create_category()
                self.create_event()
                self.create_seats()
                self.lock.release()

    def login(self, email, password):
        login_data = {
            "email": email,
            "password": password
        }
        
        response = self.client.post("/accounts/login/", data=login_data)
        
        if response.status_code == 200:
            self.client.cookies = response.cookies 
            self.csrf_token = response.cookies.get('csrftoken')  # CSRF 토큰 저장
   
    def create_category(self):
        category_data = {
            "name": "콘서트"
        }
        headers = {
            "X-CSRFToken": self.csrf_token  # CSRF 토큰을 헤더에 추가
        }
        response = self.client.post("/events/category/", json=category_data, headers=headers)

        if response.status_code == 201:
            global category_id
            category_id = response.json().get("id")

    def create_event(self):
        headers = {
            "X-CSRFToken": self.csrf_token  # CSRF 토큰을 헤더에 추가
        }
        event_data = {
            "title": "Test Post",
            "content": "This is a test post created by the first user.",
            "period_start": "2024-11-01",
            "period_end": "2024-12-01",
            "price": 0,
            "event_date": "2024-12-12",
            "category": category_id
        }
        response = self.client.post("/events/events/", json=event_data, headers=headers)

        if response.status_code == 201:
            global event_id
            event_id = response.json().get("id")

    def create_seats(self):
        global event_id, seats
        headers = {
            "X-CSRFToken": self.csrf_token  # CSRF 토큰을 헤더에 추가
        }
        seat_data = {
            "event": event_id,
            "seat": list(range(1, 1000))
        }
        self.client.post("/events/seats/", json=seat_data, headers=headers)
    
    @task
    def read_seat(self):
        global event_id
        
        response = self.client.get(f"/events/seats/?event_id={event_id}")

        if response.status_code == 200:
            seats_data = response.json()
            
            available_positions = [seat['id'] for seat in seats_data if not seat['is_reserved']]

            if len(available_positions) == 0:
                pass
            else:
                if random.random() <= 0.1:
                    self.reservation_seat(available_positions)

    @task
    def reservation_seat(self, available_positions):
        selected_seats = random.sample(available_positions, 2)
        headers = {
            "X-CSRFToken": self.csrf_token  # CSRF 토큰을 헤더에 추가
        }
        reservations = {
            "tickets": selected_seats,
        }
        response = self.client.post("/events/reservations/", json=reservations, headers=headers)

    @task
    def event_list(self):
        self.client.get("/events/events/")

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)
