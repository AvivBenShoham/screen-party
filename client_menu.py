from tkinter import *
from tkinter import messagebox
from client import client

client_online = False
myclient = None

"""tries to connect to host"""
def try_to_connect():  #no need to pass arguments to functions in both cases
    global client_online
    global myclient
    global root

    if myclient == None:

        myclient = client(root)

    try:
        x = int(port.get())
    except:
        messagebox.showinfo("ip and/or port are wrong","ip {0} and port {1} are wrong, please try again".format(hostIP.get(),port.get()))
        return

    if not myclient.set_client_and_connect(hostIP.get(), int(port.get())): #tries to connect to host by IP and Port
        messagebox.showinfo("ip and/or port are wrong","ip {0} and port {1} are wrong, please try again".format(hostIP.get(),port.get()))
        return
    else:

        client_online = True

    if not myclient.connect_to_host(password.get()): #sends password to the host
        messagebox.showinfo("password is wrong","password is wrong, please try again")
        return

    messagebox.showinfo("connection established","you have connected successfully")
    myclient.start() #gets here if the connection established and the password is right

#makes the connection frame
root = Tk()
hostIP = StringVar()
port = StringVar()
password = StringVar()

label1 = Label(root,text="enter the host IP:").grid(row=0,column=0)
label2 = Label(root,text="enter the port:").grid(row=1,column=0)
label = Label(root,text="enter the password:").grid(row=2,column=0)


ent = Entry(root,width=50,textvariable = hostIP).grid(row=0,column=1)
ent1 = Entry(root,width=50,textvariable = port).grid(row=1,column=1)
ent2 = Entry(root,width=50,textvariable = password).grid(row=2,column=1)

btn2 = Button(root, text="Connect", command=try_to_connect)

btn2.grid(row=3)
root.mainloop()