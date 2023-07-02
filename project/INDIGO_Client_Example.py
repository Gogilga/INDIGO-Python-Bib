from INDIGO_Client import INDIGOServerConnection
from colorama import Fore
import os
import signal
import time
from tabulate import tabulate
tabulate.PRESERVE_WHITESPACE = True

def connection():
    """This is a listener that is called if we lose the connection with the server. It shows a message for this reason and stops the 
    execution of the program.
    """    
    print(Fore.RED + "\n\n\t\tWe lost the connection with server\n\n" + Fore.RESET)

    # Send a signal of CONTROL-C to end the execution of the program
    p= os.getpid()
    os.kill(p,signal.SIGINT)

def connected(property):
    """In this function, we add a listener to display a message when the device in question is switched on or off.

    :param property: A property to include the listener.
    :type property: INDIGOProperty
    """
    if(property.getElementByName('CONNECTED').getValue() == 'On'):
        print("The device " + str(property.getDevice().getName()) + " is connected")
    else:
        print("The device " + str(property.getDevice().getName()) + " is disconnected")


def program():
    """This is the main part of the code. Here, there is an implementation of a small client to connect to an INDIGO server.
    First of all, you must enter a host IP address and port to connect. Lately, a small menu is displayed and you can navigate 
    it by typing the number of the option you want to select.
    """    
    host = "172.30.124.160"  # Hostname or IP of the server, you must enter your host IP address
    #host = "172.27.212.177"
    port = 7624         # Default port of INDIGO is 7624

    # Create a instance of INDIGOServerConnection
    serverConnection= INDIGOServerConnection("Server1", host, port) 

    # Create the connection
    serverConnection.connect()

    time.sleep(0.5)


    # Add some listeners
    serverConnection.addServerListener(connection)

    for device in serverConnection.getDevices():
            serverConnection.addPropertyListener(device,'CONNECTION',connected)


    # We see if connection is successful
    print("Is the server connected: " +  str(serverConnection.isConnected()) + "\n\n")

    while(serverConnection.isConnected()):
        time.sleep(0.5)

        listDevices= []
        for device in serverConnection.getDevices():

            if 'CONNECTION' in serverConnection.getDeviceByName(device).getProperties():
                # Put green color in On devices
                isON= serverConnection.getDeviceByName(device).getPropertyByName('CONNECTION').getElementByName('CONNECTED').getValue()
                if isON == 'On':
                    device= Fore.GREEN + device + Fore.RESET

            listDevices.append([device])
            
        listDevices.append(["Enable BLOB"])

        print(tabulate(listDevices, headers=['Devices'], showindex= True, tablefmt='rounded_outline', numalign="right"))

        try:
            chose= int(input("\nChoose a device for view its properties: ") or "0")
        except KeyboardInterrupt:
            #print("Has pulsed Ctrl+c for end the execute")
            break
        except ValueError:
            print("That's not int")
            chose= int(input("\nChoose a device for view its properties: ") or "0")

        # Let's remove the characters to the color for have only the name of device
        device= listDevices[chose][0]
        if Fore.GREEN in device:
            device= device.replace(Fore.GREEN, '')
            device= device.replace(Fore.RESET, '')

        if device == "Enable BLOB":
            serverConnection.enableBLOB()
        else:
            deviceChosen= serverConnection.getDeviceByName(device)

        
            listProperties= []
            for property in deviceChosen.getProperties():
                group= deviceChosen.getPropertyByName(property).getGroup()

                # Call a function to send a message to the server to put the BLOB to URL if it is activated.
                serverConnection.sendBLOBMessage(device, property)

                listProperties.append([group, property])
            
            
            listProperties.sort()

            print("\n" + tabulate(listProperties, headers=['Group', f'Properties of {device}'], showindex= True, tablefmt='rounded_outline', numalign="right"))

            try:
                chose= int(input("\nChoose a property for view its elements: ") or "0")
            except KeyboardInterrupt:
                #print("Has pulsed Ctrl+c for end the execute")
                break
            except ValueError:
                print("That's not int")
                chose= int(input("\nChoose a property for view its elements: ") or "0")

            property= listProperties[chose][1]

            propertyChosen= deviceChosen.getPropertyByName(property)
            propertyType= propertyChosen.getPropertyType()
            propertyRule= propertyChosen.getRule()

            print("\nType of property " + str(propertyType))
            print("Rule property " + str(propertyRule))
                #print("Image path: " + str(propertyPath))
                
            listElements= []
            for element in  propertyChosen.getElements():
                elementChosen= propertyChosen.getElements().get(element)
                if element == 'IMAGE':
                    listElements.append([element, elementChosen.getPath()])
                else:
                    listElements.append([element, elementChosen.getValue()])

            print("\n" + tabulate(listElements, headers=[f'Elements of {property}',  'Value'] ,showindex= True, tablefmt='rounded_outline', numalign="right"))

            try:
                chose= int(input("\nChoose a element for view its attributes: ") or "0")
            except KeyboardInterrupt:
                    #print("Has pulsed Ctrl+c for end the execute")
                break
            except ValueError:
                print("That's not int")
                chose= int(input("\nChoose a element for view its attributes: ") or "0")

            element= listElements[chose][0]
            elementChosen= propertyChosen.getElementByName(element)

            #print(elementChosen.getPath())

            # Pass the list of elements to a dicctionary
            d= dict(listElements)

            if propertyType == "Switch":
                # Put all the elements to Off.
                d = {key: "Off" for key, value in d.items()}
                d[element]= "On"

            if propertyType == "Number":
                d[element]= input("\nChoose a new value for " + element + ": ") or "0"

            if propertyType == "Text":
                d[element]= input("\nType new text for " + element + ": ") or ""

            propertyChosen.sendValues(d)
            #propertyChosen.sendValues({"TRACE":"On", "ERROR":"On"})

    serverConnection.disconnect()


# Now we run the main code to execute the program
if __name__ == "__main__":
    program()