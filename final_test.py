import RPi.GPIO as GPIO
from pad4pi import rpi_gpio
import sys
import time
import telepot
import I2C_LCD_driver
from mfrc522 import SimpleMFRC522

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

redLED = 22
greenLED = 23
buzzer = 27
relay = 4
servo = 17

GPIO.setup(buzzer, GPIO.OUT)
GPIO.setup(redLED, GPIO.OUT)
GPIO.setup(greenLED, GPIO.OUT)
GPIO.setup(relay, GPIO.OUT)
GPIO.setup(servo, GPIO.OUT)
myservo = GPIO.PWM(servo, 50)

GPIO.output(buzzer, GPIO.LOW)
GPIO.output(relay, GPIO.HIGH)
reader = SimpleMFRC522()
mylcd = I2C_LCD_driver.lcd()
menu = ""
keyInput = ""
key = ""
cardID = "729691002016"
passKey = "0606"
keyCount = 0
wrongAttempt = 0
chat_id = 1116110030
pressedSpecialKey = False

myservo.start(75)
time.sleep(1)

# Konfigurasi keypad 4x4
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

ROW_PINS = [16, 20, 21, 5]  # GPIO pins for the rows
COL_PINS = [6, 13, 19, 26]  # GPIO pins for the columns

# Inisialisasi keypad
factory = rpi_gpio.KeypadFactory()
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

# Fungsi untuk menampilkan menu
def showMenu():
    mylcd.lcd_display_string("Selamat Datang", 1, 0)
    mylcd.lcd_display_string("Pilih mode: ", 2, 0)

# Fungsi untuk menangani pilihan menu
def handleMenuChoice(choice):
    global keyCount, keyInput, pressedKey, pressedSpecialKey
    
    if choice == 'A':
        print("mode RFID aktif")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Mode: RFID", 1, 0)
        mylcd.lcd_display_string("Tempelkan kartu", 2, 0)
        id, text = reader.read()
        while id is None:
            id, text = reader.read()
        if str(id) == cardID:
            mylcd.lcd_clear()
            mylcd.lcd_display_string("ID benar,", 1, 0)
            mylcd.lcd_display_string("akses diterima", 2, 0)
            print("ID benar, buka pintu...")
            time.sleep(2)
            openDoor()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string("ID tak dikenal!", 1, 0)
            mylcd.lcd_display_string("Akses ditolak", 2, 0)
            GPIO.output(redLED, GPIO.HIGH)
            beep(3)
            GPIO.output(redLED, GPIO.LOW)
            time.sleep(1.5)
            
    elif choice == 'B':
        print("mode Keypad aktif")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Mode: Keypad", 1, 0)
        mylcd.lcd_display_string("Ketik PIN: ", 2, 0)
        while keyCount < 4:
            pressedKey = keypad.getKey()
            if pressedKey:   
                if pressedKey == "C":
                    keyCount = 0
                    keyInput = ""
                    time.sleep(0.3)
                    handleMenuChoice(choice)
                    break
                else:
                    mylcd.lcd_display_string("*", 2, keyCount+11)
                    keyInput = keyInput + str(pressedKey)
                    keyCount += 1
                    print(keyCount)
                time.sleep(0.3)
        if keyCount == 4:
            checkSpecialKey()

    else:
        print("Pilihan tidak valid")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Input tidak",1 , 0)
        mylcd.lcd_display_string("valid!",2 , 0)
        time.sleep(1.5)
        
    pressedSpecialKey = False    

def checkSpecialKey():  
    global key, keyInput, keyCount, wrongAttempt, chat_id
    
    specialKey = keypad.getKey()
    while specialKey is None:
        specialKey = keypad.getKey()
    if specialKey == 'D':
        print("memproses..")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("memproses...")
        time.sleep(2)
        if keyInput == passKey:
            mylcd.lcd_clear()
            mylcd.lcd_display_string("PIN benar,", 1, 0)
            mylcd.lcd_display_string("akses diterima", 2, 0)
            print("PIN benar, buka pintu...")
            time.sleep(2)
            openDoor()
            wrongAttempt = 4
        else:
            wrongAttempt += 1
            while wrongAttempt < 3:
                print("PIN salah")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("PIN salah!", 1, 0)
                mylcd.lcd_display_string("Coba lagi", 2, 0)
                GPIO.output(redLED, GPIO.HIGH)
                beep(2)
                GPIO.output(redLED, GPIO.LOW)
                time.sleep(1.5)
                keyCount = 0
                keyInput = ""
                handleMenuChoice(str(key))
            if wrongAttempt == 3:
                print("Mencapai 3 kali kesalahan, coba lagi nanti")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Akses ditolak!", 1, 0)
                mylcd.lcd_display_string("Tunggu 30 detik...", 2, 0)
                GPIO.output(redLED, GPIO.HIGH)
                beep(3)
                GPIO.output(redLED, GPIO.LOW)
                bot.sendMessage(chat_id, "Peringatan upaya masuk, silakan ganti passkey!")
                time.sleep(7)
                wrongAttempt = 4
                
    elif specialKey == 'C':
        keyCount = 0
        keyInput = ""
        time.sleep(0.3)
        handleMenuChoice(str(key))
    
    else:
        print("Perintah tidak valid!")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Perintah tidak", 1, 0)
        mylcd.lcd_display_string("valid!", 2, 0)
    
    keyCount = 5
    time.sleep(0.1)

def openDoor():
    mylcd.lcd_clear()
    mylcd.lcd_display_string("membuka pintu...")
    GPIO.output(relay, GPIO.LOW)
    GPIO.output(greenLED, GPIO.HIGH)
    GPIO.output(buzzer, GPIO.HIGH)
    myservo.ChangeDutyCycle(7)
    time.sleep(0.5)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(greenLED, GPIO.LOW)
    time.sleep(1)
    GPIO.output(relay, GPIO.HIGH)
    time.sleep(3)
    myservo.ChangeDutyCycle(2)
    time.sleep(0.1)
    myservo.ChangeDutyCycle(0)
    mylcd.lcd_clear()
    
def beep(period):
    for i in range(period):
        GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.2) 
        
def reset():
    global key, pressedKey, specialKey, keyInput
    
    key = ""
    pressedKey = ""
    specialKey = ""
    keyInput = ""
    
def handleTelegramMessage(msg):
    global chat_id, telegramText, telegramBotReceiveMessage, passKey
    
    chat_id = msg['chat']['id']
    telegramText = msg['text']

    print('Perintah masuk: %s' % telegramText)

    if (telegramText == "Open"):
        telegramBotReceiveMessage = True
        time.sleep(0.2)
        openDoor()
        bot.sendMessage(chat_id, "Pintu terbuka")
        
    else:
        telegramBotReceiveMessage = True
        if (telegramText[0:5] == "PASS "):
            newPassKey = telegramText.split()[1]
            if newPassKey.isdigit() and len(newPassKey) < 5:
                passKey = newPassKey
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Passkey telah", 1, 0)
                mylcd.lcd_display_string("diperbarui!", 2, 0)
                GPIO.output(greenLED, GPIO.HIGH)
                beep(2)
                GPIO.output(greenLED, GPIO.LOW)
                bot.sendMessage(chat_id, "Passkey telah diperbarui menjadi {}".format(passKey))
                print("Passkey diperbarui menjadi {}".format(passKey))
                time.sleep(2)
                mylcd.lcd_clear()
            else:
                GPIO.output(redLED, GPIO.HIGH)
                beep(2)
                GPIO.output(redLED, GPIO.LOW)
                print("Format passkey {} tidak valid!".format(newPassKey))
                bot.sendMessage(chat_id, "Format passkey {} tidak valid!".format(newPassKey))
        else:
            GPIO.output(redLED, GPIO.HIGH)
            beep(2)
            GPIO.output(redLED, GPIO.LOW)
            print("Perintah tidak valid!")
            bot.sendMessage(chat_id, "Perintah tidak valid!")
    telegramBotReceiveMessage = False

telegramBotRun = False
telegramBotReceiveMessage = False
# Program utama
try:
    while True:
        time.sleep(0.1)
        if telegramBotRun == False:
            bot = telepot.Bot('5681863680:AAG77Iisoz6DlhDhx-rpaZdlmfKysnDgjns')
            bot.message_loop(handleTelegramMessage)
            telegramBotRun = True
            print(telegramBotRun)

        time.sleep(0.1)
        if telegramBotReceiveMessage == False:
            showMenu()
        
        #print("Tekan tombol pada keypad untuk memilih opsi...")
        key = keypad.getKey()
        if key:
            print("Anda menekan tombol:", key)
            mylcd.lcd_display_string(key, 2, 12)
            time.sleep(1)
            handleMenuChoice(str(key))
            time.sleep(0.1)  # Tunggu sebentar untuk menghindari membaca berulang dari satu penekanan tombol
            mylcd.lcd_clear()
            wrongAttempt = 0
            keyCount = 0
            reset()
            print("\n")    
                                
except KeyboardInterrupt:
    print("Program dihentikan.")
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Program berhenti!", 1, 0)
    keypad.cleanup()
    GPIO.cleanup()
finally:
    keypad.cleanup()
    GPIO.cleanup()
