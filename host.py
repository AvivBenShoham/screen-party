#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import threading
import win32api
import netifaces
import time
from mss import mss
from pynput import mouse
from pynput import keyboard
from tkinter import messagebox
import select
import random
import logging
import zlib

from host_menu import *

class host:

    """creates class variables who doesn't  belong to host's socket"""
    def __init__(self):
        logging.basicConfig(filename="example.log",level=logging.DEBUG)
        self.ip = None
        self.server_socket = socket.socket()
        self.client_sockets = []
        self.master = Tk()

        self.password = str(random.randint(100000,999999))
        self.menuButtons = []

        self.mouse = mouse.Controller()
        self.keyboard = keyboard.Controller()

        self.num_of_connections = 0
        self.locked_mouse_events = []
        self.locked_keyboard_events = []

        self.host_menu = host_menu(self.master, self.get_local_ip(), self.initiated)

    """ called after the host set his IP and Port, opens a socket with those variables and starts the execution. """
    def initiated(self):
        self.host_menu.setup()
        self.ip = self.host_menu.get_ip()
        self.port = int(self.host_menu.get_port())
        self.host_menu.start_menu.destroy()
        self.server_socket.bind((self.ip,self.port))
        self.server_socket.listen(10)

        self.start()

    """starts the new connections thread, makes the control panel widget and moves on to the mainloop thread"""
    def start(self):
        accept_client_thread = threading.Thread(name="connections",target=self.connect_to_client)
        accept_client_thread.setDaemon(True)
        accept_client_thread.start()

        Label(self.master, text="your IP is: " + self.ip).pack()
        Label(self.master, text="your password is: " + self.password).pack()
        Label(self.master, text="the connection port is: " + str(self.port)).pack()
        button = Button(self.master,text="Close",command=self.quit).pack()
        self.master.protocol("WM_DELETE_WINDOW",self.quit)

        self.run()

    """the mainloop infinite loop, responsible to the data transfers to connected clients"""
    def run(self):
        if self.get_number_of_connections() > 0:
            for client in self.client_sockets:
                try:
                    start_time = time.time()
                    screenshot_size,screenshot_bytes = self.capture_screenshot()
                    bytes = zlib.compress(screenshot_bytes) #compressed screenshot bytes
                    self.send_screenshot(screenshot_size,bytes,client[0])
                    self.handle_mouse_and_keyboard(client)
                    logging.debug("sendscreenshot time: "+str(time.time() - start_time))
                except Exception as e:
                    logging.error(e)
                    for x in self.menuButtons:
                        if x['text'] == str(client[1][0]) + str(" ") + str(client[1][1]):
                            client_button = x
                    self.remove_client(client_button,client)
        self.master.after(40,self.run)

    """removes specific client from connected clients"""
    def remove_client(self,mb,client):
        mb.destroy()
        self.num_of_connections = self.num_of_connections-1
        self.client_sockets.remove(client)

    """adds client to host's control panel """
    def add_client_toCP(self, client):
        mb = Menubutton(self.master, width=50, text=client[1], relief=RAISED)
        mb.menu = Menu(mb, tearoff=0)
        mb["menu"] = mb.menu
        mb.menu.add_command(label="dis/able mouse",
                            command=lambda client1=client,permission="mouse": self.disableOrAble_client(
                                client1, permission))
        mb.menu.add_command(label="dis/able keyboard",
                            command=lambda client1=client,permission="keyboard": self.disableOrAble_client(
                                client1, permission))
        mb.menu.add_command(label="disconnect client",
                            command=lambda client1=client: self.remove_client(mb,client1))
        mb.pack()
        self.menuButtons.append(mb)

    """appends/removes client from the specific permission access list """
    def disableOrAble_client(self,client,typeOfPermission):
        if typeOfPermission == "mouse":
            if client in self.locked_mouse_events:
                self.locked_mouse_events.remove(client)
            else:
                self.locked_mouse_events.append(client)
        else:
            if client in self.locked_keyboard_events:
                self.locked_keyboard_events.remove(client)
            else:
                self.locked_keyboard_events.append(client)

    """return self.num_of_connections """
    def get_number_of_connections(self):
        return self.num_of_connections

    """sends screenshot's size and compressed bytes in client_socket """
    def send_screenshot(self,size,raw_bytes,client_socket):
        done = False
        num_of_bytes = size.width*size.height*4
        a = str(size.width)+str(",")+str(size.height)+str(",")+str(len(raw_bytes))
        a = a.ljust(max(1024, 0))
        a = a.encode("utf-8")
        client_socket.send(a)

        while not done: #sends the raw_bytes in 1024 bytes packets
            if num_of_bytes<1024:
                client_socket.send(raw_bytes)
                break
            client_socket.send(raw_bytes[0:1024])
            raw_bytes = raw_bytes[1024:]
            num_of_bytes -= 1024

    """capture screenshot as bytes and size and returns them"""
    def capture_screenshot(self):
        # Capture entire screen
        with mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            return sct_img.size, sct_img.bgra  #scr_img.bgra means raw bytes

    """update mouse cords according to the received client mouse move, sends back the new mouse cords """
    def mouse_cords_update(self,client):
        client_mouse_move = client[0].recv(1024) #receives encoded str: x mouse move , y mouse move
        client_mouse_move = client_mouse_move.split(b'\0', 1)[0]
        client_mouse_move = client_mouse_move.decode("utf-8")
        client_mouse_move = client_mouse_move.split(",")  # type: 'str'
        if len(client_mouse_move) < 2:
            return
        mouse_pos = win32api.GetCursorPos()  # type: 'int'

        if client not in self.locked_mouse_events:
            new_x = (mouse_pos[0] + int(client_mouse_move[0]))
            new_y = (mouse_pos[1] + int(client_mouse_move[1]))
            win32api.SetCursorPos((new_x, new_y))
            mouse_package = str(new_x) + str(",") + str(new_y)
            mouse_package = mouse_package.ljust(max(1024, 0))
            client[0].send(mouse_package.encode("utf-8")) # sends encoded mouse pos: x cords , y cords
        else:
            mouse_package = str(mouse_pos[0])+ str(",")+str(mouse_pos[1])
            mouse_package = mouse_package.ljust(max(1024, 0))
            client[0].send(mouse_package.encode("utf-8")) # sends encoded mouse pos: x cords , y cords

    """receives mouse and keyboard events and executes them """
    def handle_mouse_and_keyboard(self,client):
        self.mouse_cords_update(client)
        rlist, wlist, elist = select.select([client[0]], [], [], 0.005)
        events = None

        for sock in rlist:

            events = sock.recv(1024) #tries to recieve package of mouse and keyboard events of client.
            events = events.split(b'\0', 1)[0]
            events = events.decode("utf-8")
            events = events.split(";") #the package is encoded actions list cells seperated by ";"

        if events == None:
            return

        for x in range(0,len(events),1): #passes the list we receives from the client and executes the events.

            enable = client not in self.locked_mouse_events #contains boolean var of client's permission to control mouse

            if events[x] == "Button1-pressed":
                logging.debug("button1 pressed")
                if enable: self.mouse.press(mouse.Button.left)

            elif events[x] == "Button1-released":
                logging.debug("button1 released")
                if enable: self.mouse.release(mouse.Button.left)

            elif events[x] == "Button3-pressed":
                logging.debug("button3 pressed")
                if enable: self.mouse.press(mouse.Button.right)

            elif events[x] == "Button3-released":
                logging.debug("button3 released")
                if enable: self.mouse.release(mouse.Button.right)

            elif events[x] == "Double1":
                logging.debug("Double1 pressed")
                if enable: self.mouse.click(mouse.Button.left,2)


            elif events[x] == "Double3":
                logging.debug("Double3 pressed")
                if enable: self.mouse.click(mouse.Button.right,2)

            elif "mousewheel" in events[x]:
                events[x] = events[x].split(",")
                if enable: self.mouse.scroll(0, events[x][1])

            else:
                enable = client not in self.locked_keyboard_events

                if events[x] == "Enter":
                    if enable: self.keyboard.press(keyboard.Key.enter)

                elif events[x] == "Shift":
                    if enable: self.keyboard.press(keyboard.Key.shift)

                elif events[x] == "space":
                    if enable: self.keyboard.press(keyboard.Key.space)

                elif "ctrl" in events[x]:
                    if enable:
                        self.keyboard.press(keyboard.Key.ctrl)
                        events[x] = events[x][-1]
                        logging.debug("ctrl: "+events[x])
                        self.keyboard.press(events[x])
                        self.keyboard.release(keyboard.Key.ctrl)

                elif events[x] == "down_arrow":
                    if enable: self.keyboard.press(keyboard.Key.down)

                elif events[x] == "up_arrow":
                    if enable: self.keyboard.press(keyboard.Key.up)

                elif events[x] == "left_arrow":
                    if enable: self.keyboard.press(keyboard.Key.left)

                elif events[x] == "right_arrow":
                    if enable: self.keyboard.press(keyboard.Key.right)

                elif events[x].strip() != "":
                    if enable:
                        logging.debug("event = {0}".format(events[x].strip()))
                        self.keyboard.press(events[x])
                        self.keyboard.release(events[x])

    """tries to accept new clients, when client made a connection, sends him to a new thread of connection"""
    def connect_to_client(self):
        while True:
            try:
                (client_socket, client_address) = self.server_socket.accept()
                connect_thread = threading.Thread(name="connection", target=self.accept_client,args=[client_socket,client_address])
                connect_thread.setDaemon(True)
                connect_thread.start()
            except:
                pass

    """tries to receive a password from connected client, appends client to the connected clients list only when the password is right"""
    def accept_client(self,client_socket,client_address):
        while True:
            try:
                password = client_socket.recv(1024)
                password = password.decode("utf-8")
                logging.debug(password)
                if self.password == password:
                    package = "accepted"
                    package = package.ljust(max(1024, 0))
                    package = package.encode("utf-8")
                    client_socket.send(package)
                    time.sleep(1)
                    self.num_of_connections = self.get_number_of_connections() + 1
                    self.client_sockets.append([client_socket, client_address])
                    self.add_client_toCP(self.client_sockets[-1])
                    break
            except():
                pass

    """ returns list of the computer optional IPs"""
    def get_local_ip(self):
        local_ips = []
        local_ip = ""
        for netiface in netifaces.interfaces():
            x = netifaces.ifaddresses(netiface)[netifaces.AF_INET]
            for num in range(0,len(x),1):
                ip = x[num]['addr']
                local_ips.append(ip)
            logging.debug (x)
        return local_ips

    """closes all client connections and ends the program"""
    def quit(self):
        self.client_sockets = []
        messagebox.showinfo("End of connection","Thank you for using our program. The program has been ended")
        self.master.destroy()
        quit()



if __name__ == '__main__':
    h = host()

    h.master.mainloop()