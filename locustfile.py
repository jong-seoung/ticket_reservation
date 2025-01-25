from locust import HttpUser, TaskSet, task, between
import random
import string
import logging
import time


class UserBehavior(TaskSet):
    logger = logging.getLogger("locust_test")
    category_id = None
    event_id = 1

    def on_start(self):
        """
        테스트가 시작될 때 실행.
        사용자 회원가입 및 로그인 처리.
        """
        # 동적 사용자 정보 생성
        name = f'{random.randint(1,100)}'.join(random.choices(string.ascii_letters + string.digits, k=5)).lower()
        site = ''.join(random.choices(string.ascii_letters + string.digits, k=6)).lower()
        domain = ''.join(random.choices(string.ascii_letters + string.digits, k=3)).lower()
        email = f"{name}@{site}.{domain}"
        password = "password123!"
        phone_number = f"010{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        birthday = f"{random.randint(1980, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

        # CSRF, 세션 쿠키
        self.csrf_token = None  # CSRF 토큰 초기화
        self.session_cookies = None  # 세션 쿠키 초기화
        self.headers = None # 헤더 초기화

        # 회원가입 요청
        self.register_user(name, email, password, phone_number, birthday)

    def register_user(self, name, email, password, phone_number, birthday):
        """
        사용자 회원가입 요청 처리.
        """
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "phone_number": phone_number,
            "birthday": birthday
        }
        response = self.client.post("/accounts/register/", json=payload)

        if response.status_code == 201:
            self.logger.info(f"User {email} registered successfully.")
            time.sleep(10)
            self.login(email, password)
        else:
            self.logger.error(f"Registration failed: {response.status_code} - {response} - {payload}")


    def login(self, email, password):
        """
        사용자 로그인 요청 처리.
        """
        payload = {
            "email": email,
            "password": password
        }
        response = self.client.post("/accounts/login/", json=payload)

        if response.status_code == 200:
            self.session_cookies = response.cookies
            self.csrf_token = response.cookies.get("csrftoken")
            self.headers = {
                "X-CSRFToken": self.csrf_token
            }
            self.logger.info(f"User {email} login in successfully.")
        else:
            self.logger.error(f"login failed: {response.status_code} - {response} - {payload}")


    def on_stop(self):
        """사용자가 종료될 때 실행"""
        self.client.post("/accounts/logout/", headers=self.headers)

    @task
    def get_profile(self):
        """
        사용자 프로필 가져오기.
        """
        response = self.client.get("/accounts/profile/", headers=self.headers)
        if response.status_code == 200:
            self.logger.info("Get profile successfully.")
        else:
            self.logger.error(f"Failed to Get profile: {response.status_code} - {response.text}")

    # def create_category(self):
    #     category_data = {
    #         "name": "콘서트"
    #     }
    #     response = self.client.post("/events/category/", json=category_data, headers=self.headers)

    #     if response.status_code == 201:
    #         self.category_id = response.json().get("id")
    #         self.create_event()
    #     else:
    #         self.logger.error(f"Create_category failed: {response.status_code}")


    # def create_event(self):
    #     event_data = {
    #         "title": "Test Post",
    #         "content": "This is a test post created by the user.",
    #         "period_start": "2024-11-01",
    #         "period_end": "2024-12-01",
    #         "price": 0,
    #         "event_date": "2024-12-12",
    #         "category": self.category_id
    #     }
    #     response = self.client.post("/events/events/", json=event_data, headers=self.headers)

    #     if response.status_code == 201:
    #         self.event_id = response.json().get("id")
    #         self.create_seats()
    #     else:
    #         self.logger.error(f"Registration failed: {response.status_code} - {response.text}")


    # def create_seats(self):
    #     seat_data = {
    #         "event": self.event_id,
    #         "seat": list(range(1, 100))
    #     }
    #     self.client.post("/events/seats/", json=seat_data, headers=self.headers)
    
    # @task
    # def read_seat(self):
    #     response = self.client.get(f"/events/seats/?event_id={self.event_id}")

    #     if response.status_code == 200:
    #         seats_data = response.json()
            
    #         available_positions = [seat['id'] for seat in seats_data if not seat['is_reserved']]

    #         if len(available_positions) == 0:
    #             pass
    #         else:
    #             self.reservation_seat(available_positions)

    # def reservation_seat(self, available_positions):
    #     selected_seats = random.sample(available_positions, 1)
    #     reservations = {
    #         "tickets": selected_seats,
    #     }
    #     response = self.client.post("/events/reservations/", json=reservations, headers=self.headers)

    # @task
    # def event_list(self):
    #     self.client.get("/events/events/")

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(5, 10)