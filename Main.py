import requests
import json
import time
from recap_token import RecaptchaSolver

class TicketBooking:
    def __init__(self, user_data_file, recaptcha_token):
        self.s = requests.Session()
        self.recaptcha_token = recaptcha_token
        self.load_user_data(user_data_file)
        self.eng_team = 'Al Ahly FC'
        self.team_id = 77  # ID الأهلي
        self.notified_matches = set()

    def load_user_data(self, user_data_file):
        with open(user_data_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
            self.username = lines[0]
            self.password = lines[1]
            self.search_word = lines[2]
            self.seats = lines[3]
            self.category = lines[4]

    def get_headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://tazkarti.com/',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
        }

    def get_available_matches(self):
        url = 'https://tazkarti.com/data/matches-list-json.json'
        try:
            res = self.s.get(url, headers=self.get_headers()).text
            matches = json.loads(res)
            return [match for match in matches if (match['teamName1'] == self.eng_team or match['teamName2'] == self.eng_team) and match['matchStatus'] == 1]
        except Exception as e:
            print(f"❌ خطأ في تحميل المباريات: {e}")
            return []

    def check_match_tickets(self, match):
        match_id = match['matchId']
        if match_id in self.notified_matches:
            return  # تم الإشعار بالفعل

        url = f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{match_id}.json'
        try:
            res = self.s.get(url, headers=self.get_headers()).text
            data = json.loads(res)['data']
        except Exception as e:
            print(f"❌ خطأ في تحميل تذاكر المباراة {match_id}: {e}")
            return

        message = f"🎟️ المباراة بين: {match['teamName1']} و {match['teamName2']}\n"
        message += "📋 قائمة الدرجات:\n"
        ticket_found = False

        for cat in data:
            if int(cat['teamId']) == self.team_id:
                message += f"- الفئة: {cat['categoryName']} | المقاعد: {cat['availableSeats']} | السعر: {cat['price']} جنيه\n"
                if cat['availableSeats'] > 0:
                    ticket_found = True

        # أرسل إشعار مرة واحدة فقط
        self.send_telegram_notification(message)
        self.notified_matches.add(match_id)

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

    def run_monitor(self):
        print("⏳ جاري مراقبة تذاكر الأهلي ...")
        while True:
            matches = self.get_available_matches()
            for match in matches:
                self.check_match_tickets(match)
            time.sleep(10)

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
    booking = TicketBooking('data.txt', tok)
    booking.login()
    booking.run_monitor()
