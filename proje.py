import socket
import tkinter as tk
from threading import Thread
import time
import queue

# Sunucu ayarları
UDP_IP = "127.0.0.1"
UDP_PORT = 5005 #alıcı ve verici portu için istenilen port numarası atanabilir.
BUFFER_SIZE = 1024

# Kullanıcı arayüzü oluşturma
class App(tk.Tk):
    def __init__(self):
        super().__init__() #app sınıfı için tk.Tk sınıfının özelliklerini çağırır.
        self.title("Ethernet Veri Alışverişi")
        self.geometry("400x350")

        self.response_messages = {
            "0xC1": "Cevap Mesajı 1",
            "0xC2": "Cevap Mesajı 2",
            "0xC3": "Cevap Mesajı 3",
            "0xC4": "Cevap Mesajı 4",
            "0xC5": "Cevap Mesajı 5"
        }

        self.message_label = tk.Label(self, text="Gelen Mesaj:")
        self.message_label.pack() #pack metodu nesneyi arayüze yerleştirir.

        self.message_box = tk.Text(self, height=5, width=40) #gelen mesajlar için mesaj kutusu
        self.message_box.pack()

        self.response_label = tk.Label(self, text="Cevap Mesajı:")
        self.response_label.pack()

        self.response_entry = tk.Entry(self) #girdi için tkinkerin tk.Entry sınıfını kullandık.
        self.response_entry.pack()

        self.delay_label = tk.Label(self, text="Gönderme Gecikmesi (saniye):")
        self.delay_label.pack()

        self.delay_entry = tk.Entry(self)
        self.delay_entry.pack()

        self.send_button = tk.Button(self, text="Cevap Gönder", command=self.send_response) #cevap gönder'e tıklandığında send_response yöntemi çağrılacak.
        self.send_button.pack()

        self.connection_status = tk.Label(self, text="Bağlantı Durumu: Bağlanıyor...")
        self.connection_status.pack()

        self.request_queue = queue.Queue()

        self.server_thread = Thread(target=self.run_server) #server_thread adında bir iş parçacığı oluşturduk ve çalıştığında run_server yöntemini çağıracak
        self.server_thread.daemon = True #bu değer programın kapanınca thread'ın da kapanacağını belirtir.
        self.server_thread.start() #iş parçacığını yani threadı başlatır

        self.client_thread = Thread(target=self.run_client) #aynı işlemler client için
        self.client_thread.daemon = True
        self.client_thread.start()

        self.check_connection_thread = Thread(target=self.check_connection) #aynı işlemler bağlantı için
        self.check_connection_thread.daemon = True
        self.check_connection_thread.start()

    def run_server(self): #sunucu threadının çalıştığı run_server fonksiyonu
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #python socket programlama ile socketi belirledik, AF_INET IPv4 için, SOCK_DGRAM UDP protokolü için
        server_socket.bind((UDP_IP, UDP_PORT)) #serverin bağlanacağı ip ve port adresini belirledik.

        self.connection_status.config(text="Bağlantı Durumu: Bağlandı") #eğer sunucu bağlanırsa, connection_status'u bağlandı olarak değiştirir.

        while True: #sunucu sürekli mesajları dinlesin.
            data, addr = server_socket.recvfrom(BUFFER_SIZE) #data değişkenine serverdan gelen mesaj depolanırken, adrr'ye ip ve port depolanır.
            message = data.decode("utf-8") #byte ile gelen veri metne dönüştürülür.
            self.message_box.insert("1.0", message + "\n") #alınan mesaj, pencerede 1.0'da yani başlangıç konumuna yazılır.
            self.save_received_message(message) #mesaj save_received_message metoduna gönderilerek kaydedilir..

            response = self.response_entry.get()
            if response in self.response_messages: #eğer gönderilecek cevap response_messages içinde yer alıyorsa ilgili fonksiyona gönder.
                self.request_queue.put(response)

    def run_client(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_messages = [
            "0x11: 1. Mesaj",
            "0x12: 2. Mesaj",
            "0x13: 3. Mesaj",
            "0x14: 4. Mesaj",
            "0x15: 5. Mesaj"
        ]

        try:
            client_socket.connect((UDP_IP, UDP_PORT))
            self.connection_status.config(text="Bağlantı Durumu: Bağlandı")
        except Exception as e: #exception türündeki e değişkenine hatayı kaydettik.
            self.connection_status.config(text="Bağlantı Durumu: Bağlantı Hatası")

        for message in client_messages:
            client_socket.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))
            time.sleep(1)  # Gecikme ayarı

    def save_received_message(self, message):
        with open("received_messages.txt", "a") as f:
            f.write(message + "\n")

    def save_sent_response(self, response):
        with open("sent_responses.txt", "a") as f: #with ile kullandığımızdan bellek kaynaklarını verimli kullanmış oluruz.
            f.write(response + "\n")

    def send_response(self):
        response = self.response_entry.get()
        if response in self.response_messages: #gönderilen mesaj, gönderilecek mesajlar içerisinde var mı kontrol ettik.
            response_delay = float(self.delay_entry.get()) #kullanıcı arayüzünden alınan gecikme süresini response_delay'e atadık.
            time.sleep(response_delay)  # Gecikmeyi burada uygulayalım.
            response_message = self.response_messages[response]
            self.message_box.insert("1.0", "Cevap gönderildi: " + response_message + "\n")
            self.save_sent_response(response_message)
        else:
            self.message_box.insert("1.0", "Geçersiz cevap mesajı!\n")

    def process_requests(self):
        while True:
            try:
                response = self.request_queue.get(block=True, timeout=0.1) #block true parametresi eğer kuyruk boşsa cevap bekletir. Yeni mesaj gelene kadar kuyruk timout kadar bloklanır.
                self.send_response()
            except queue.Empty:
                pass

    def check_connection(self):
        while True:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client_socket.connect((UDP_IP, UDP_PORT))
                self.connection_status.config(text="Bağlantı Durumu: Bağlandı")
            except Exception as e:
                self.connection_status.config(text="Bağlantı Durumu: Bağlantı Koptu")
            time.sleep(2)  # Bağlantı durumunu kontrol aralığı


if __name__ == "__main__":
    app = App()
    app.mainloop() #kullanıcı arayüzünü başlatır ve arayüzü kapatana kadar programın çalışmasını sürdürdük
