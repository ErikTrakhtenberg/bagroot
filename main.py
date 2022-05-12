import threading
import socket
import subprocess
from tkinter import *
import folium
from folium.plugins import MarkerCluster
from tkinter import messagebox as ms
import os
import pandas as pd
import sqlite3
import winrt.windows.devices.geolocation as wdg, asyncio


class Cl:
    def __init__(self, username):
        self.username = username
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(('127.0.0.1', 59000))
        self.run_client()

    # noinspection PyBroadException
    def client_receive(self):
        while True:
            try:
                message = self.client.recv(2048).decode('utf-8')
                if message == "alias?":
                    self.client.send(self.username.encode('utf-8'))
                else:
                    print(message)
            except:
                print('Error!')
                self.client.close()
                break

    def client_send(self):
        while True:
            message = f'{self.username}: {input("")}'
            self.client.send(message.encode('utf-8'))

    def send(self):
        try:
            self.client.send(self.username.encode('utf-8'))
        finally:
            self.client.send("ERROR".encode('utf-8'))

    def run_client(self):
        receive_thread = threading.Thread(target=self.client_receive())
        receive_thread.start()

        send_thread = threading.Thread(target=self.client_send())
        send_thread.start()


class MainWindow:
    def __init__(self, master, userID):
        self.master = master
        self.userID = userID
        self.master.geometry("800x360")
        self.master.resizable(0, 9999)
        self.shareID = 1
        self.UI()

    # gets the coordinates of the user
    async def getCoords(self):
        locator = wdg.Geolocator()
        pos = await locator.get_geoposition_async()
        return [pos.coordinate.latitude, pos.coordinate.longitude]

    # converts coordinates into a usable list
    def getLoc(self):
        return asyncio.run(self.getCoords())

    # generates a folium map html file and runs it
    def generate_map(self):
        try:
            host = socket.gethostbyname("www.google.com")
            socket.create_connection((host, 80), 2)
        except:
            ms.showinfo("Error", "No wifi detected. make sure you're connected to a wifi")
            return
        location = self.getLoc()
        location[0] = round(location[0], 6)
        location[1] = round(location[1], 6)
        db = sqlite3.connect('database.db')
        df = pd.read_sql_query('SELECT * from mapdata WHERE userID =' + str(self.userID[0]), db)
        db.close()
        wifi_map = folium.Map(location=location, zoom_start=10, control_scale=True)
        cluster = MarkerCluster(name="cluster").add_to(wifi_map)
        for (index, row) in df.iterrows():
            if row.loc['wifiPass'] is not None:
                folium.Marker([row.loc['longitude'], row.loc['latitude']],
                              popup=("name:" + str(row.loc['wifiName']) + " " + "password:" + str(row.loc['wifiPass'])),
                              icon=folium.Icon(color="green", icon='fa-light fa-wifi', prefix='fa'),
                              tooltip="click for more info") \
                    .add_to(cluster)
            else:
                folium.Marker([row.loc['longitude'], row.loc['latitude']],
                              popup=("name:" + str(row.loc['wifiName']) + " " + "no password"),
                              icon=folium.Icon(color="red", icon='fa-light fa-wifi', prefix='fa'),
                              tooltip="wifi with no password. " + "click for more info") \
                    .add_to(cluster)

        folium.Marker(location, tooltip="your current location",
                      icon=folium.Icon(color="blue", icon='fa-light fa-circle', prefix='fa')).add_to(cluster)
        wifi_map.save('map.html')
        os.system("start \"\" map.html")

    # gets the currently connected wifi name and password
    def get_current_wifi(self):
        try:
            host = socket.gethostbyname("www.google.com")
            socket.create_connection((host, 80), 2)
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8').split('\n')
            wifi = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'])
            h = wifi.decode('utf-8').split('\n')
            h = [c.split(":")[1][1:-1] for c in h if "SSID" in c]
            profiles = [i.split(":")[1][1:-1] for i in data if "All User Profile" in i]
            for i in profiles:
                results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode(
                    'utf-8').split('\n')
                results = [b.split(":")[1][1:-1] for b in results if "Key Content" in b]
                if str(h[0]) == str(i):
                    try:
                        return [i, results[0]]
                    except IndexError:
                        return [i, None]

        except:
            pass
        return

    def add_wifi(self, name_and_password, userID):
        try:
            host = socket.gethostbyname("www.google.com")
            socket.create_connection((host, 80), 2)
        except:
            ms.showinfo("Error", "No wifi detected. make sure you're connected to a wifi")
            return
        location = self.getLoc()
        location[0] = round(location[0], 6)
        location[1] = round(location[1], 6)
        with sqlite3.connect('database.db') as db:
            c = db.cursor()
            find_wifi = ('SELECT wifiName FROM mapdata WHERE wifiName = ? AND userID= ' + str(self.userID[0]))
            c.execute(find_wifi, [name_and_password[0]])
            if c.fetchall():
                ms.showinfo('Error!', 'wifi already exists in your account')
            else:
                # Create Account
                insert = 'INSERT INTO mapdata(longitude,latitude,wifiName,wifiPass,userID) VALUES(?,?,?,?,?)'
                c.execute(insert,
                          [location[0], location[1], str(name_and_password[0]), str(name_and_password[1]), userID[0]])
                ms.showinfo('Success!', 'wifi added!')
                db.commit()
                self.UI()
        return

    def share(self):
        self.shareUI()

    def back(self):
        self.map_button1.destroy()
        self.logout_button1.destroy()
        self.share_button1.destroy()
        self.entry1.destroy()
        self.top_label1.destroy()
        self.top_row_name1.destroy()
        self.top_row_pass1.destroy()
        self.top_row_long1.destroy()
        self.top_row_lat1.destroy()
        self.UI()

    def UI(self):
        my_conn = sqlite3.connect('database.db')
        select = 'SELECT wifiName,wifiPass,longitude,latitude from mapdata WHERE userID= ?'
        self.wifi_list = my_conn.execute(select, self.userID)
        self.top_label = Label(self.master, text="your wifi list", font='Arial 15 bold underline')
        self.top_label.grid(row=0, column=2)
        self.top_row_name = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_name.grid(row=1, column=0)
        self.top_row_name.insert(END, "name of wifi")
        self.top_row_pass = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_pass.grid(row=1, column=1)
        self.top_row_pass.insert(END, "password")
        self.top_row_long = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_long.grid(row=1, column=2)
        self.top_row_long.insert(END, "longitude")
        self.top_row_lat = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_lat.grid(row=1, column=3)
        self.top_row_lat.insert(END, "latitude")
        i = 2  # row value inside the loop
        for ID in self.wifi_list:
            for j in range(len(ID)):
                self.entry = Entry(self.master, width=25, fg='black')
                self.entry.grid(row=i, column=j)
                if ID[j] is None:
                    self.entry.insert(END, "No password")
                else:
                    self.entry.insert(END, ID[j])
            i = i + 1
        self.map_button = Button(self.master, text=' generate map ', bd=2, relief="solid", font=("Rubik", 15),
                                 bg="#2acc53", padx=5, pady=5, width=12, command=lambda: self.generate_map())
        self.map_button.place(x=640, y=20)
        self.add_button = Button(self.master, text=' add wifi ', bd=2, relief="solid", font=("Rubik", 15),
                                 bg="#34baf7", padx=5, pady=5,
                                 width=12, command=lambda: self.add_wifi(self.get_current_wifi(), self.userID))
        self.add_button.place(x=640, y=80)
        self.share_button = Button(self.master, text=' share ', bd=2, relief="solid", font=("Rubik", 15),
                                   bg="white", padx=5, pady=5, width=12, command=lambda: self.share())
        self.share_button.place(x=640, y=140)
        self.logout_button = Button(self.master, text=' log out ', bd=2, relief="solid", font=("Rubik", 15),
                                    bg="red", padx=5, pady=5, width=12, command=lambda: self.log_out())
        self.logout_button.place(x=640, y=200)

    def shareUI(self):
        my_conn = sqlite3.connect('database.db')
        select = 'SELECT wifiName,wifiPass,longitude,latitude from mapdata WHERE userID= ?'
        self.wifi_list1 = my_conn.execute(select, [self.shareID])
        temp = str(self.get_share_username()[0])
        temp2 = temp.replace("('", "")
        self.share_username = temp2.replace("',)", "")
        self.top_label1 = Label(self.master, text=str(self.share_username) + "'s wifi list",
                                font='Arial 15 bold underline')
        self.top_label1.grid(row=0, column=2)
        self.top_row_name1 = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_name1.grid(row=1, column=0)
        self.top_row_name1.insert(END, "name of wifi")
        self.top_row_pass1 = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_pass1.grid(row=1, column=1)
        self.top_row_pass1.insert(END, "password")
        self.top_row_long1 = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_long1.grid(row=1, column=2)
        self.top_row_long1.insert(END, "longitude")
        self.top_row_lat1 = Entry(self.master, width=25, fg='black', bg="#d1d1d1", relief="solid")
        self.top_row_lat1.grid(row=1, column=3)
        self.top_row_lat1.insert(END, "latitude")
        i = 2  # row value inside the loop
        for ID in self.wifi_list1:
            for j in range(len(ID)):
                self.entry1 = Entry(self.master, width=25, fg='black')
                self.entry1.grid(row=i, column=j)
                if ID[j] is None:
                    self.entry1.insert(END, "No password")
                else:
                    self.entry1.insert(END, ID[j])
            i = i + 1
        self.wifi_list1.close()
        self.map_button1 = Button(self.master, text=' generate map ', bd=2, relief="solid", font=("Rubik", 15),
                                  bg="#2acc53", padx=5, pady=5, width=12, command=lambda: self.generate_map())
        self.map_button1.place(x=640, y=20)
        self.share_button1 = Button(self.master, text=' back ', bd=2, relief="solid", font=("Rubik", 15),
                                    bg="white", padx=5, pady=5, width=12, command=lambda: self.back())
        self.share_button1.place(x=640, y=140)
        self.logout_button1 = Button(self.master, text=' add wifi ', bd=2, relief="solid", font=("Rubik", 15),
                                     bg="#34baf7", padx=5, pady=5, width=12, state=DISABLED)
        self.logout_button1.place(x=640, y=80)

    def get_share_username(self):
        with sqlite3.connect('database.db') as db:
            crsr = db.cursor()
        get_shareID = 'SELECT username FROM users WHERE ID=?'
        crsr.execute(get_shareID, [self.shareID])
        result = crsr.fetchall()
        return result

    def log_out(self):
        self.master.destroy()
        root = Tk()
        root.title('Wifi map login')
        LogReg(root)
        root.mainloop()


# login Class
class LogReg:
    def __init__(self, master):
        self.master = master
        self.master.resizable(0, 0)
        self.username = StringVar()
        self.password = StringVar()
        self.n_username = StringVar()
        self.n_password = StringVar()
        self.logingUI()

    # noinspection PyBroadException
    def login(self):
        # Establish Connection
        with sqlite3.connect('database.db') as db:
            crsr = db.cursor()
        # Find user If there is any take proper action
        find_user = 'SELECT * FROM users WHERE username = ? and password = ?'
        crsr.execute(find_user, [(self.username.get()), (self.password.get())])
        result = crsr.fetchall()
        if result:
            try:
                # Cl(self.username.get())
                self.main_screen(self.username.get())
            except:
                ms.showerror('Error!', 'no server connection')
                self.main_screen(self.username.get())
        else:
            ms.showerror('Oops!', 'Username or password incorrect.')

    def new_user(self):
        # Establish Connection
        with sqlite3.connect('database.db') as db:
            c = db.cursor()
        # Find Existing username
        find_user = 'SELECT username FROM users WHERE username = ?'
        c.execute(find_user, [(self.n_username.get())])
        if c.fetchall():
            ms.showerror('Error!', 'Username Taken Try a Different One.')
        else:
            ms.showinfo('Success!', 'Account Created!')
            self.back()
            # Create Account
            insert = 'INSERT INTO users(username,password) VALUES(?,?)'
            c.execute(insert, [(self.n_username.get()), (self.n_password.get())])
            db.commit()

        # Frame Packing Methods

    def back(self):
        self.username.set('')
        self.password.set('')
        self.crf.pack_forget()
        self.head['text'] = 'Login to your Account'
        root.title('Wifi map login')
        self.logf.pack()

    def cr(self):
        self.n_username.set('')
        self.n_password.set('')
        self.logf.pack_forget()
        self.head['text'] = 'Create an Account'
        root.title('Wifi map register')
        self.crf.pack()

    def main_screen(self, username):
        ms.showinfo("Success!", "Logged in!")
        self.destroy()
        root = Tk()
        root.title(username + 's wifi list')
        with sqlite3.connect('database.db') as db:
            crsr = db.cursor()
        get_userID = 'SELECT ID FROM users WHERE username = ? and password = ?'
        crsr.execute(get_userID, [(self.username.get()), (self.password.get())])
        result = crsr.fetchall()
        MainWindow(root, result[0])
        root.mainloop()

    def toggle_password(self):
        if self.password_entry.cget('show') == '':
            self.password_entry.config(show='*')
        else:
            self.password_entry.config(show='')

    def toggle_password2(self):
        if self.password_entry2.cget('show') == '':
            self.password_entry2.config(show='*')
        else:
            self.password_entry2.config(show='')

    # Widgets
    def logingUI(self):
        self.head = Label(self.master, text='Login to your account', width="25", height="1", font=("Arial", 25, 'bold'),
                          pady=11)
        self.head.pack()
        # self.backbutton = Button(self.master, text='⟵', relief="flat", font=("Robotto", 13, "bold"), padx=8, pady=3, command=self.runmain)
        # self.backbutton.place(x=0,y=0) #backbutton to main ERIK DONT FORGET
        self.logf = Frame(self.master, padx=10, pady=10)
        self.username_label = Label(self.logf, text='username: ', font=("Rubik", 20), pady=5, padx=5)
        self.username_label.grid(sticky=W)
        self.username_entry = Entry(self.logf, textvariable=self.username, bd=1, relief="solid", font=('', 15))
        self.username_entry.grid(row=0, column=1)
        self.password_label = Label(self.logf, text='password: ', font=("Rubik", 20), pady=5, padx=5)
        self.password_label.grid(sticky=W)
        self.password_entry = Entry(self.logf, textvariable=self.password, bd=1, relief="solid", font=('', 15),
                                    show='*')
        self.password_entry.grid(row=1, column=1)
        self.login_button = Button(self.master, text=' login ', bd=2, relief="solid", font=("Rubik", 15), bg="#2A99CC",
                                   padx=5, pady=5, command=self.login)
        self.login_button.place(x=85, y=176)
        self.register_button = Button(self.logf, text=' register ', bd=2, relief="solid", font=("Rubik", 15),
                                      bg="#2A99CC", padx=5, pady=5, command=self.cr)
        self.register_button.grid(row=2, column=1)
        self.eye_button = Button(self.logf, text="👁", font=("Arial bold", 20), padx=0, pady=0, width="2",
                                 relief="flat",
                                 command=self.toggle_password)
        self.eye_button.grid(row=1, column=2)
        self.logf.pack()

        self.crf = Frame(self.master, padx=10, pady=10)
        self.username_label2 = Label(self.crf, text='username: ', font=("Rubik", 20), pady=5, padx=5)
        self.username_label2.grid(sticky=W)
        self.username_entry2 = Entry(self.crf, textvariable=self.n_username, bd=1, relief="solid", font=("Robotto", 15))
        self.username_entry2.grid(row=0, column=1)
        self.password_label2 = Label(self.crf, text='password: ', font=("Rubik", 20), pady=5, padx=5)
        self.password_label2.grid(sticky=W)
        self.password_entry2 = Entry(self.crf, textvariable=self.n_password, bd=1, relief="solid", font=("Robotto", 15),
                                     show='*')
        self.password_entry2.grid(row=1, column=1)
        self.create_button = Button(self.crf, text='create account', bd=2, relief="solid", font=("Rubik", 15),
                                    bg="#2A99CC", padx=5, pady=5, command=self.new_user)
        self.create_button.place(x=0, y=100)
        self.gotologin_button = Button(self.crf, text='go to login', bd=2, relief="solid", font=("Robotto", 15),
                                       bg="#2A99CC", padx=5, pady=5, command=self.back)
        self.gotologin_button.grid(row=2, column=1)
        self.eye_button2 = Button(self.crf, text="👁", font=("Arial bold", 20), padx=0, pady=0, width="2",
                                  relief="flat",
                                  command=self.toggle_password)
        self.eye_button2.grid(row=1, column=2)

    def destroy(self):
        self.head.pack_forget()
        self.logf.pack_forget()
        self.crf.pack_forget()
        self.login_button.destroy()
        self.master.destroy()

    # def runmain2(self):
    #     self.head.pack_forget()
    #     self.backbutton.pack_forget()
    #     self.logf.pack_forget()
    #     self.crf.pack_forget()
    #     self.login_button.destroy()
    #     self.master.geometry("400x300")
    #     main2.MainMenu(self.master,self.username.get())


# make database and users (if not exists already) table at programme start up
with sqlite3.connect('database.db') as db:
    crsr = db.cursor()
crsr.execute(
    'CREATE table IF NOT EXISTS "users" ("ID"INTEGER NOT NULL,"username"	TEXT NOT NULL UNIQUE,"password"	TEXT NOT '
    'NULL,PRIMARY KEY( '
    '"ID"));')
crsr.execute('CREATE table IF NOT EXISTS "mapdata" ("mapID"	INTEGER NOT NULL UNIQUE,"longitude"	INTEGER NOT NULL,'
             '"latitude" '
             'INTEGER NOT NULL,"wifiName"	TEXT NOT NULL UNIQUE,"wifiPass"	TEXT,"userID"	INTEGER,PRIMARY KEY('
             '"mapID"),FOREIGN KEY("userID") REFERENCES "users"("ID"));')
db.commit()
db.close()

if __name__ == '__main__':
    root = Tk()
    root.title('Wifi map login')
    LogReg(root)
    root.mainloop()
