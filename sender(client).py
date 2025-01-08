import cv2
import numpy as np
import socket
import pyautogui
import tkinter as tk
from tkinter import scrolledtext, simpledialog
import threading
import time

# Configuring
SCREEN_PORT = 8080
CHAT_PORT = 5555
DEST_IP = "127.0.0.1" 
stop_sharing = False

# Sockets
screen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connects to the chat server
def connect_chat_server():
    global chat_sock
    chat_sock.connect((DEST_IP, CHAT_PORT))
    name = simpledialog.askstring("Name", "Enter your name:")
    chat_sock.send(name.encode('utf-8'))
    threading.Thread(target=receive_chat_messages, daemon=True).start()

# Receives chat messages
def receive_chat_messages():
    while True:
        try:
            message = chat_sock.recv(1024).decode('utf-8')
            if message:
                update_chat_display(message)
        except:
            print("Chat server disconnected.")
            break

# Sends chat messages
def send_chat_message():
    message = chat_entry.get()
    chat_entry.delete(0, tk.END)
    if message:
        chat_sock.send(message.encode('utf-8'))
        update_chat_display(f"You: {message}")

# Updates chat display in GUI
def update_chat_display(message):
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, message + "\n")
    chat_display.config(state=tk.DISABLED)


def start_screen_sharing():
    global stop_sharing
    stop_sharing = False
    while not stop_sharing:
        screen = pyautogui.screenshot()
        frame = np.array(screen)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (640, 480))
        result, encoded_frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if result:
            screen_sock.sendto(encoded_frame.tobytes(), (DEST_IP, SCREEN_PORT))

        time.sleep(0.05)  # Adding a delay (20 FPS) to prevent flickering


# Stops screen sharing
def stop_screen_sharing():
    global stop_sharing
    stop_sharing = True

# Closes application
def on_close():
    stop_screen_sharing()
    chat_sock.close()
    screen_sock.close()
    root.destroy()

# GUI
root = tk.Tk()
root.title("Screen Sharing Sender with Chat")
root.protocol("WM_DELETE_WINDOW", on_close)

start_button = tk.Button(root, text="Start Screen Sharing", command=lambda: threading.Thread(target=start_screen_sharing, daemon=True).start())
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Screen Sharing", command=stop_screen_sharing)
stop_button.pack(pady=10)

chat_display = scrolledtext.ScrolledText(root, state='disabled', width=50, height=10)
chat_display.pack(pady=10)

chat_entry = tk.Entry(root, width=50)
chat_entry.pack(pady=5)

send_button = tk.Button(root, text="Send", command=send_chat_message)
send_button.pack(pady=5)

# Start chat server connection
connect_chat_server()

root.mainloop()
