import tkinter as tk
from tkinter import *
from tkinter import ttk


class host_menu:

    """makes a start menu widget of the host, the host chooses his parameters (IP and Port)"""
    def __init__(self, root, ip_list, initiated):
        self.start_menu = Toplevel(root)
        self.start_menu.geometry('400x100')

        label = Label(self.start_menu,text= "Choose your IP: ").grid(row=1,column=0)
        label = Label(self.start_menu,text= "enter the connection port: ").grid(row=2,column=0)

        self.ip_combo = ttk.Combobox(self.start_menu, values=ip_list)
        self.ip_combo.grid(row=1,column=1)

        self.port_variable = StringVar()

        self.port_entry = Entry(self.start_menu, width=50, textvariable=self.port_variable)
        self.port_entry.grid(row=2,column=1)

        self.setup_button = Button(self.start_menu, text="Set up", command=initiated)
        self.setup_button.grid()

    """updates up and port according to the input on the widget"""
    def setup(self):
        self.ip = self.ip_combo.get()
        self.port = self.port_variable.get()
        print("ip = {0}, port = {1}".format(self.ip, self.port))

    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

def main():
    root = tk.Tk()
    my_menu = host_menu(root, ["127.0.0.1", "200.100.200.130"])

    root.mainloop()

if __name__ == '__main__':
    main()