import requests
import json
import time
from recap_token import RecaptchaSolver

class TicketBooking:
    def __init__(self, user_data_file, recaptcha_token):
        self.s = requests.Session()
        self.wait = 0
        self.recaptcha_token = recaptcha_token
        self.load_user_data(user_data_file)
        self.possible_seat_locations = self.determine_seat_locations()
        self.teams = self.initialize_teams()
        self.found = False
        self.team_name = "2929292922"
        self.match_id = None
        self.category_id = None
        self.team_id = None
        self.match_team_zone_id = None
        self.price = None
        self.match_team_1 = ""
        self.match_team_2 = ""

    def load_user_data(self, user_data_file):
        with open(user_data_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
            self.username = lines[0]
            self.password = lines[1]
            self.search_word = lines[2]
            self.seats = lines[3]
            self.category = lines[4]

    def determine_seat_locations(self):
        if "درج" in self.category and "ول" in self.category:
            return ["Cat 1", "Cat1"]
        elif "درج" in self.category and "اني" in self.category:
            return ["Cat 2", "Cat2"]
        elif "تالت" in self.category or "ثالث" in self.category:
            return ["Cat 3", "Cat3"]
        elif "مقصو" in self.category:
            return ["VIP"]
        elif "علو" in self.category:
            return ["Upper"]
        elif "سفل" in self.category:
            return ["Lower"]
        else:
            return []

    def initialize_teams(self):
        return {
            'سماع': {'team_name': 'الاسماعيلى', 'eng_team': 'ISMAILY SC', 'categoryName': 'ISMAILY', 'teamid': '182'},
            'زمالك': {'team_name': 'الزمالك', 'eng_team': 'Zamalek SC', 'categoryName': 'Zamalek', 'teamid': '79'},
            'هل': {'team_name': 'الأهلى', 'eng_team': 'Al Ahly FC', 'categoryName': 'Ahly', 'teamid': '77'},
            'مصر': {'team_name': 'النادي المصري للألعاب الرياضية', 'eng_team': 'Al-Masry SC', 'categoryName': 'Al-Masry'}
        }

    def find_team_info(self):
        for key in self.teams:
            if key in self.search_word:
                self.found = True
                team_info = self.teams[key]
                self.team_name = team_info['team_name']
                self.eng_team = team_info['eng_team']
                self.category_name = team_info['categoryName']
                self.team_id = team_info['teamid']
                return

    def wait_for_registration(self):
        while True:
            try:
                h = self.get_headers()
                res = self.s.get('https://tazkarti.com/data/matches-list-json.json', headers=h).text
                if self.team_name in res:
                    return res
                else:
                    self.wait += 1
                    print(f'\rمنتظر فتح الحجز ... لا تغلق البرنامج: {self.wait}', end='')
                    time.sleep(2)
            except Exception as ee:
                print(ee)

    def get_headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://tazkarti.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }

    def get_match_id(self, res):
        matches = json.loads(res)
        for match in matches:
            if match["teamName1"] == self.eng_team or match["teamName2"] == self.eng_team:
                if match.get('matchStatus') == 1:
                    self.match_id = match["matchId"]
                    self.match_team_1 = match["teamName1"]
                    self.match_team_2 = match["teamName2"]
                    return
        exit()

    def check_loop_for_tickets(self):
        while True:
            if self.check_ticket_once():
                break
            print("لا توجد تذاكر متاحة حالياً. إعادة المحاولة خلال 10 ثوانٍ ...")
            time.sleep(10)

    def check_ticket_once(self):
        url = f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{self.match_id}.json'
        r1 = self.s.get(url, headers=self.get_headers()).text
        r1_data = json.loads(r1)

        available_tickets = []
        for category in r1_data['data']:
            if category['categoryName'].strip().lower() == self.category_name.strip().lower():
                available_tickets.append({
                    'category': category['categoryName'],
                    'available_seats': category['availableSeats'],
                    'price': category['price'],
                })
            else:
                for seat in self.possible_seat_locations:
                    if seat.lower() in category['categoryName'].strip().lower() and int(self.team_id) == category['teamId']:
                        available_tickets.append({
                            'category': category['categoryName'],
                            'available_seats': category['availableSeats'],
                            'price': category['price'],
                        })

        if available_tickets:
            message = f"🎟️ المباراة بين: {self.match_team_1} و {self.match_team_2}\n"
            message += "🚨 التذاكر متاحة الآن:\n"
            for ticket in available_tickets:
                message += f"- الفئة: {ticket['category']} | {ticket['available_seats']} مقعد | السعر: {ticket['price']} جنيه\n"
            print(message)
            self.send_telegram_notification(message)
            return True
        return False

    def send_telegram_notification(self, message):
        telegram_token = '7696180515:AAG3mOyADlsdKv_jqatlmPP25LJI9AwaIPM'
        chat_id = '6589167323'
        url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
        payload = {'chat_id': chat_id, 'text': message}
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print("✅ تم إرسال التنبيه عبر Telegram.")
            else:
                print("❌ فشل إرسال التنبيه عبر Telegram.")
        except Exception as e:
            print(f"❌ خطأ في إرسال تنبيه Telegram: {e}")

    def login(self):
        headers = self.get_headers()
        headers.update({'Content-Type': 'application/json'})
        json_data = {
            'Username': self.username,
            'Password': self.password,
            'recaptchaResponse': self.recaptcha_token,
        }
        r = self.s.post('https://tazkarti.com/home/Login', headers=headers, json=json_data).text
        tok = r.split('access_token":"')[1].split('"')[0]

if __name__ == '__main__':
    solver = RecaptchaSolver('https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LeypS8dAAAAAGWYer3FgEpGtmlBWBhsnGF0tCGZ&co=aHR0cHM6Ly90YXprYXJ0aS5jb206NDQz&hl=en&v=9pvHvq7kSOTqqZusUzJ6ewaF&size=invisible&cb=376av9ky8egv')
    tok = solver.get_token()
    booking = TicketBooking(r'C:\Users\mohamed\Documents\Auto-Booking-Tazkarti-Ticket-main\data.txt', tok)

    booking.find_team_info()
    res = booking.wait_for_registration()
    booking.get_match_id(res)
    booking.login()
    booking.check_loop_for_tickets()
