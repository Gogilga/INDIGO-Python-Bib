import tkinter
import tkinter.messagebox
import customtkinter
import time
from colorama import Back, Fore
from INDIGO_Client import INDIGOServerConnection
from INDIGO_Client import INDIGODevice

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

list_radiobuttons= []

"""def connected(property):
    if(property.getElementByName('CONNECTED').getValue() == 'On'):
        print("The device " + str(property.getDevice().getName()) + " is connected")
    else:
        print("The device " + str(property.getDevice().getName()) + " is disconnected")"""


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.deviceChosen= tkinter.StringVar()
        self.lastDeviceChosen= tkinter.StringVar()
        self.propertyChosen= tkinter.StringVar()
        self.elementChosen= tkinter.StringVar()

        host = "172.30.124.160"  # Hostname or IP of server
        #host = "172.27.212.177"
        port = 7624         # Default port of INDIGO is 7624

        # Create a instance of INDIGOServerConnection
        self.serverConection= INDIGOServerConnection("Server1", host, port)

        # Create the connection
        self.serverConection.connect()

        
        self.serverConection.addServerListener(self.conection)

        time.sleep(0.5)

        # configure window
        self.title("INDIGO")
        self.geometry(f"{1200}x{580}")

        # create a menubar
        self.menubar = tkinter.Menu(self)
        self.config(menu=self.menubar)

        # create a menu
        self.file_menu = tkinter.Menu(self.menubar)
        
        # add a menu item to the menu
        self.file_menu.add_command(
            label='Exit',
            command=self.destroy
        )

        # add the File menu to the menubar
        self.menubar.add_cascade(
            label="File",
            menu=self.file_menu
        )

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)


        self.scrollable_frame_1 = customtkinter.CTkScrollableFrame(self, label_text="Server " + host, width=300)
        self.scrollable_frame_1.grid(row=0, column=0, rowspan=8, sticky="nsew")
        self.scrollable_frame_1.grid_columnconfigure(0, weight=1)

        for device in self.serverConection.getDevices():
            self.serverConection.addPropertyListener(device,'CONNECTION',self.connected)

        self.devices()
        
        self.scrollable_frame_2 = customtkinter.CTkScrollableFrame(self, label_text= "Device", width=300)
        self.scrollable_frame_2.grid(row=0, column=1, rowspan=8, sticky="nsew")
        self.scrollable_frame_2.grid_columnconfigure(0, weight=1)

        self.scrollable_frame_3 = customtkinter.CTkScrollableFrame(self, label_text= "Elements", width=500)
        self.scrollable_frame_3.grid(row=0, column=2, rowspan=8, sticky="nsew")
        self.scrollable_frame_3.grid_columnconfigure(0, weight=1)

    def devices(self):
        if(self.serverConection.isConnected()):
            time.sleep(0.5)

            listDevices= []
            for device in self.serverConection.getDevices():
                listDevices.append(device)
            r= 1

            if self.deviceChosen:
                self.lastDeviceChosen= self.deviceChosen

            for device in listDevices:

                radio_button = customtkinter.CTkRadioButton(self.scrollable_frame_1, command=self.pulseDevice, text= device, value= device, variable=self.deviceChosen)
                radio_button.grid(row=r, column=0, padx=20, pady=10, sticky="wn")

                if 'CONNECTION' in self.serverConection.getDeviceByName(device).getProperties():
                    # Put some color in On devices
                    isON= self.serverConection.getDeviceByName(device).getPropertyByName('CONNECTION').getElementByName('CONNECTED').getValue()
                    if isON == 'On':
                        #device= Fore.GREEN + device + Fore.RESET
                        radio_button.configure(text_color='#50fa7b')

                
                r+=1

        else:
            self.scrollable_frame_2.insert("0.0", "Server is disconnected")

    def connected(self, property):
        time.sleep(1.0)
        print("here")
        print(self.deviceChosen.get())

        # if self.scrollable_frame_3:
        #     for widgets in self.scrollable_frame_3.winfo_children():
        #         widgets.destroy()

        self.devices()

        self.sidebar_button_event(self.deviceChosen.get())

        self.sidebar_button_event_2()



    def conection(self):
        print("Server is disconnected")
        for widgets in self.winfo_children():
            
            if widgets != self.menubar:
                widgets.destroy()

        self.scrollable_frame_4= customtkinter.CTkTextbox(self, height=50, width=300)
        self.scrollable_frame_4.grid(row=0, column=0, rowspan=8, columnspan= 3, padx=20, pady=10)
        self.scrollable_frame_4.insert("0.0", "Server is disconnected")
        self.scrollable_frame_4.configure(state="disabled")  # configure textbox to be read-only

        time.sleep(2)
        self.destroy

    def send_changes(self):
        d= {}
        if self.propertyC.getPropertyType() == "Text":
            for elem in self.textboxes:
                d[elem]= self.textboxes[elem].get(1.0, "end-1c")
            
            print(d)

            self.propertyC.sendValues(d)


    def OneOfMany_pulse(self):
        elementC= self.propertyC.getElementByName(self.elementChosen.get())
        
        d= {}
        if elementC.getValue() == "Off":
            d[self.elementChosen.get()]= "On"
        else:
            d[self.elementChosen.get()]= "Off"

        self.propertyC.sendValues(d)

    def checkbox_pulse(self):
        print(self.elementChosen.get())

    def sidebar_button_event_2(self):
        self.propertyC= self.deviceC.getPropertyByName(self.propertyChosen.get())

        for widgets in self.scrollable_frame_3.winfo_children():
            widgets.destroy()

        self.scrollable_frame_3.configure(label_text= "Elements of " + self.propertyChosen.get())

        listElements= []
        for element in  self.propertyC.getElements():
            el= self.propertyC.getElements().get(element)
            listElements.append([element, el.getValue()])

        self.checkboxes= {}
        self.textboxes= {}
        r= 1
        for element, value in listElements:
            if (self.propertyC.getPropertyType()) == 'Switch' and (self.propertyC.getRule() == 'OneOfMany'):
                radio_button= customtkinter.CTkRadioButton(self.scrollable_frame_3, command=self.OneOfMany_pulse, text= element, value= element, variable=self.elementChosen)
                radio_button.grid(row=r, column=0, padx=20, pady=10, sticky="wn")
                r+=1

                if value == 'On':
                    radio_button.select()

            elif self.propertyC.getPropertyType() == 'Switch':
                self.checkboxes[element]= customtkinter.CTkCheckBox(self.scrollable_frame_3, command=self.checkbox_pulse, text= element, variable=self.elementChosen)
                self.checkboxes[element].grid(row=r, column=0, padx=20, pady=10, sticky="wn")
                r+=1

                if value == 'On':
                    self.checkboxes[element].select()

            elif self.propertyC.getPropertyType() == 'Text':
                self.textboxes[element]= customtkinter.CTkTextbox(self.scrollable_frame_3, height=50, width=300)
                self.textboxes[element].grid(row=r, column=0, padx=20, pady=10, sticky="wn")
                self.textboxes[element].insert("0.0", str(value))
                r+=1

                if self.propertyC.getPerm() == "ro":
                    self.textboxes[element].configure(state="disabled")  # configure textbox to be read-only

            else:
                radio_button = customtkinter.CTkRadioButton(self.scrollable_frame_3, command=self.sidebar_button_event_2, text= element, value= element, variable=self.elementChosen)
                radio_button.grid(row=r, column=0, padx=20, pady=10, sticky="wn")
                r+=1

        if not (self.propertyC.getRule() == 'OneOfMany') and not (self.propertyC.getPerm() == "ro"):
            self.button= customtkinter.CTkButton(self.scrollable_frame_3, text="Send changes", command=self.send_changes)
            self.button.grid(row=r, column=0, padx=20, pady=10, sticky="wn")

    def pulseDevice(self):
        self.sidebar_button_event(self.deviceChosen.get())

    def sidebar_button_event(self, device):
        self.deviceC= self.serverConection.getDeviceByName(device)

        print(f"Last Device chosen {self.lastDeviceChosen.get()}\n")
        print(f"Device {device}\n")


        if list_radiobuttons:
            for radio_button in list_radiobuttons:
                # print(type(radio_button))
                # print(radio_button.cget("text"))
                radio_button.destroy()
            list_radiobuttons.clear()

        """for widgets in self.scrollable_frame_2.winfo_children():
            widgets.destroy()"""


        self.scrollable_frame_2.configure(label_text= device)

        listProperties= []
        for property1 in self.deviceC.getProperties():
            listProperties.append(property1)

        r= 1
        for property in listProperties:
            radio_button = customtkinter.CTkRadioButton(self.scrollable_frame_2, command=self.sidebar_button_event_2, text= property, value= property, variable=self.propertyChosen)

            if self.propertyChosen.get() == self.deviceC.getPropertyByName(property):
                radio_button.select()

            list_radiobuttons.append(radio_button)

        for p in list_radiobuttons:
            p.grid(row=r, column=0, padx=20, pady=10, sticky="wn")
            r+=1


        
        #print(self.scrollable_frame_2.winfo_children()[0].winfo_children())


if __name__ == "__main__":
    app = App()
    app.mainloop()