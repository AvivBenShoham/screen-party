import base64
import io
import socket
import time
import win32api
import zlib
from io import StringIO
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import select
import logging

class client():

    def __init__(self, root):
        logging.basicConfig(filename='example.log', level=logging.DEBUG)
        self.my_socket = None
        self.mouse_cords = win32api.GetCursorPos()
        self.master = Toplevel(root)

    """gets ip and port and tries to connect to them"""
    def set_client_and_connect(self, ip, port):
        try:
            if self.my_socket==None:
                self.my_socket = socket.socket()
                self.my_socket.settimeout(1)
                self.my_socket.connect((ip, port))
        except socket.error:
            self.my_socket = None
            return False

        return True

    """sets graphic settings, creates the widget which shows host's screen and binds to all keyboard and mouse events on the widget"""
    def graphic_settings(self):
        im = Image.open("C:\\Users\\User\\no-signal.png")
        ph = ImageTk.PhotoImage(im)
        self.label = Label(self.master,width=1920,height=1080)
        self.label.image = ph
        self.label.configure(image=ph)
        self.master.config(cursor="arrow")
        self.label.pack()
        self.actions = []
        self.master.focus_set()
        self.master.bind("<Double-Button-1>", lambda event, a="Double1":self.double_pressed(a))
        self.master.bind("<Double-Button-3>", lambda event, a="Double3":self.double_pressed(a))
        self.master.bind('<Button-1>', lambda event, a="Button1": self.button_pressed(a))
        self.master.bind('<ButtonRelease-1>', lambda event, a="Button1": self.button_released(a))
        self.master.bind('<Button-3>', lambda event, a="Button3": self.button_pressed(a))
        self.master.bind('<ButtonRelease-3>', lambda event, a="Button3": self.button_released(a))
        self.master.bind("<MouseWheel>", self.mousewheel)
        self.master.bind('<Key>', self.key_entered)
        self.master.bind('<Return>',lambda event,a="Enter": self.speical_key(a))
        self.master.bind('<Control-Shift-Up>', lambda event,a="Shift": self.speical_key(a))
        self.master.bind('<space>',lambda event, a="space": self.speical_key(a))
        self.master.bind('<Left>',lambda event,a="left_arrow":self.speical_key(a))
        self.master.bind('<Right>',lambda event,a="right_arrow":self.speical_key(a))
        self.master.bind('<Up>',lambda event,a="up_arrow":self.speical_key(a))
        self.master.bind('<Down>',lambda event,a="down_arrow":self.speical_key(a))
        self.ctrl_binds()
        self.master.protocol("WM_DELETE_WINDOW", self.quit)

    """binds to all ctrl+key"""
    def ctrl_binds(self):
        x = 'a'
        for y in range(0,26,1):
            self.master.bind('<Control-{}>'.format(x),lambda event,key=x: self.ctrl(key))
            x = chr(ord(x)+1)

    """receive image bytes and size and returns them"""
    def receive_screenshot(self):
        done = False
        size = self.my_socket.recv(1024)
        size = size.split(b'\0')[0]
        size = size.decode("utf-8")
        size = size.split(",")
        num_of_bytes = int(size[2])
        size.remove(size[2])
        image_bytes = bytes()
        while num_of_bytes > 0:
            data = self.my_socket.recv(1024)
            image_bytes += data
            num_of_bytes -= len(data)
        return image_bytes,size

    """calls graphic settings proc and starts the mainloop loop """
    def start(self):
        self.graphic_settings()
        self.start_time = time.time()
        self.master.update()

        self.run()

    """the mainloop loop, responsible to data transfers with the host """
    def run(self):
        try:
            data,size = self.receive_screenshot()
            self.display_screenshot(data,size)
            self.handle_events()
            self.master.after(40, self.run)
        except Exception as e:
            logging.error(e)
            self.quit()

    """handle mouse and keyboard events """
    def handle_events(self):
        self.update_mouse_cords()
        self.send_mouse_and_keyboard_events()

    """sends client mouse move to host, receives new mouse cords and update the mouse cords. """
    def update_mouse_cords(self):
        client_mouse = win32api.GetCursorPos()
        last_move = []
        last_move.append(client_mouse[0] - self.mouse_cords[0])
        last_move.append(client_mouse[1] - self.mouse_cords[1])
        mouse_move_package= str(last_move[0]) + str(",") + str(last_move[1])
        mouse_move_package = mouse_move_package.ljust(max(1024,0))
        self.my_socket.send(mouse_move_package.encode("utf-8")) #sends encoded str of: x mouse move, y mouse move
        mouse_cords = self.my_socket.recv(1024) # receives new mouse cords: encoded str of x mouse cords, y mouse cords

        #decoding...
        mouse_cords = mouse_cords.split(b'\0', 1)[0]
        mouse_cords = mouse_cords.decode("utf-8")
        mouse_cords = mouse_cords.split(",")

        self.mouse_cords = []
        self.mouse_cords.append(int(mouse_cords[0]))
        self.mouse_cords.append(int(mouse_cords[1]))
        win32api.SetCursorPos((self.mouse_cords[0],self.mouse_cords[1])) #sets new mouse cords

    """sends mouse and keyboard presses """
    def send_mouse_and_keyboard_events(self):
        actions_to_do = ""
        if len(self.actions) == 0:
            return

        for x in range(0,len(self.actions),1):
            actions_to_do = actions_to_do+self.actions[x]+";"
        actions_to_do = actions_to_do.ljust(max(1024, 0))
        self.my_socket.send(actions_to_do.encode("utf-8"))
        actions_to_do = ""
        self.actions = []

    """turns the image bytes into image and displays it in the widget """
    def display_screenshot(self,image_data,size):
        data = zlib.decompress(image_data)
        img = Image.frombytes('RGB',(int(size[0]),int(size[1])), data, 'raw', 'BGRX') # turns the bytes into image
        photo = ImageTk.PhotoImage(img)
        self.label.image = photo
        self.label.configure(image=photo)

    """tries to connect to host by sending password"""
    def connect_to_host(self, password):
        try:
            #time.sleep(0.05)
            #password = input("password of host")
            self.my_socket.send(password.encode("utf-8"))
            rlist,wlist,elist = select.select([self.my_socket],[],[],1)
            for sock in rlist:
                answer = sock.recv(1024)
                logging.debug(len(answer))
                answer = answer.decode("utf-8")
                answer = answer.split(" ")[0]
                logging.debug(answer)
                return answer=="accepted"
                #if answer == "accepted":
                #    self.run()
        except:
            return False

    """appends to actions list str of the event"""
    def button_pressed(self,B_number):
        self.actions.append(str(B_number)+"-pressed")

    """appends to actions list str of the event"""
    def button_released(self,B_number):
        self.actions.append(str(B_number)+"-released")

    """appends to actions list str of the event"""
    def mousewheel(self,event):
        self.actions.append("mousewheel,"+str(event.delta))

    """appends to actions list str of the event"""
    def double_pressed(self,a):
        logging.debug("double")
        self.actions.append(str(a))

    """appends to actions list str of the event"""
    def key_entered(self,event):
        logging.debug(event.char)
        self.actions.append(event.char)

    """appends to actions list str of the event"""
    def ctrl(self,a):
        logging.debug("ctrl-"+a)
        self.actions.append(("ctrl-"+str(a)))

    """appends to actions list str of the event"""
    def speical_key(self,a):
        logging.debug("special key "+a)
        self.actions.append(a)

    """ends the connection"""
    def quit(self):
        messagebox.showinfo("End of connection","thanks for using our program, the connection has been ended")
        quit()


if __name__ == '__main__':
    c = client()
    c.master.mainloop()