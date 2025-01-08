import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np
import datetime
import time

# Configuration
CHAT_PORT = 5555
SCREEN_PORT = 8080
clients = []
client_names = []

# UDP socket for screen sharing
screen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
screen_sock.bind(("0.0.0.0", SCREEN_PORT))

# TCP socket for chat
chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Function to broadcast chat messages to all connected clients
def broadcast(message, sender_socket=None):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                remove(client)

# Removes a client from the list of active connections
def remove(client):
    if client in clients:
        index = clients.index(client)
        name = client_names[index]
        clients.remove(client)
        client_names.remove(name)
        broadcast(f"{name} has left the chat.".encode('utf-8'))

#Handles chat
def handle_client(connection, address):
    connection.send("Enter your name: ".encode('utf-8'))
    name = connection.recv(1024).decode('utf-8')
    client_names.append(name)
    clients.append(connection)
    broadcast(f"{name} has joined the chat.".encode('utf-8'))

    while True:
        try:
            message = connection.recv(1024)
            if message:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                formatted_message = f"{timestamp} {name}: {message.decode('utf-8')}\n"
                broadcast(formatted_message.encode('utf-8'), connection)
                update_chat_display(formatted_message)
            else:
                remove(connection)
                break
        except:
            continue

# Starts the chat server
def start_chat_server():
    chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_server.bind(("0.0.0.0", CHAT_PORT))
    chat_server.listen(5)
    print("Chat server started. Waiting for connections...")
    while True:
        connection, address = chat_server.accept()
        threading.Thread(target=handle_client, args=(connection, address), daemon=True).start()

# GUI
def update_chat_display(message):
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, message)
    chat_display.config(state=tk.DISABLED)

# Recieves screen frames
def receive_screen_frames():
    prev_time = time.time()
    while True:
        data, _ = screen_sock.recvfrom(65536)
        np_array = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            
            current_time = time.time()
            if current_time - prev_time > 0.05: 
                prev_time = current_time
                frame_label.imgtk = img_tk
                frame_label.configure(image=img_tk)


# Connects to chat server for sending messages
def connect_to_chat_server():
    chat_sock.connect(("127.0.0.1", CHAT_PORT))
    threading.Thread(target=receive_chat_messages, daemon=True).start()

# Receives messages from the chat server
def receive_chat_messages():
    while True:
        try:
            message = chat_sock.recv(1024).decode('utf-8')
            if message:
                update_chat_display(message)
        except:
            break

# Sends chat messages
def send_chat_message():
    message = chat_entry.get()
    chat_entry.delete(0, tk.END)
    if message:
        chat_sock.send(message.encode('utf-8'))

# Closes application gracefully
def on_close():
    screen_sock.close()
    chat_sock.close()
    root.destroy()

# Creates the GUI
root = tk.Tk()
root.title("Screen Sharing Receiver with Chat")
root.protocol("WM_DELETE_WINDOW", on_close)

frame_label = tk.Label(root)
frame_label.pack()

chat_display = scrolledtext.ScrolledText(root, state='disabled', width=50, height=10)
chat_display.pack(pady=10)

chat_entry = tk.Entry(root, width=50)
chat_entry.pack(pady=5)

send_button = tk.Button(root, text="Send", command=send_chat_message)
send_button.pack(pady=5)

# Start threads for chat server and screen sharing
threading.Thread(target=start_chat_server, daemon=True).start()
threading.Thread(target=receive_screen_frames, daemon=True).start()
connect_to_chat_server()

root.mainloop()
