import INDIGO_Client
from INDIGO_Client import INDIGOServerConection
from colorama import Back, Fore
import os
import signal
import time
from tabulate import tabulate
tabulate.PRESERVE_WHITESPACE = True

def conection():
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

def temperature(property):
    if(int(property.getElementByName('ALT_POLAR_ERROR').getValue()) > 0):
        print("The ALT_POLAR_ERROR of " + str(property.getDevice().getName()) + " is greater than 0.")
    #print(property)


# Now we run the main code to execute the program
if __name__ == "__main__":
    host = "172.30.124.160"  # Hostname or IP of the server, you must enter your host IP address
    #host = "172.27.212.177"
    port = 7624         # Default port of INDIGO is 7624

    # Create a instance of INDIGOServerConection
    serverConection= INDIGOServerConection("Server1", host, port)

    # Create the connection
    serverConection.connect()

    time.sleep(0.5)


    # Add some listeners
    serverConection.addPropertyListener('CCD Guider Simulator','SIMULATION_SETUP',temperature)

    serverConection.addServerListener(conection)

    for device in serverConection.getDevices():
            serverConection.addPropertyListener(device,'CONNECTION',connected)


    # We see if connection is successful
    print("Is the server connected: " +  str(serverConection.isConnected()) + "\n\n")

    while(serverConection.isConnected()):
        time.sleep(0.5)

        listDevices= []
        for device in serverConection.getDevices():

            if 'CONNECTION' in serverConection.getDeviceByName(device).getProperties():
                # Put green color in On devices
                isON= serverConection.getDeviceByName(device).getPropertyByName('CONNECTION').getElementByName('CONNECTED').getValue()
                if isON == 'On':
                    device= Fore.GREEN + device + Fore.RESET

            listDevices.append([device])

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


        deviceChosen= serverConection.getDeviceByName(device)

        """listProperties= []
        for property in deviceChosen.getProperties():
            listProperties.append([property])
            #deviceChosen.getPropertyByName(property).getLight()
            print(deviceChosen.getPropertyByName(property).getMessage())
            print(deviceChosen.getPropertyByName(property).getGroup())

        print("\n" + tabulate(listProperties, headers=[f'Properties of {device}'], showindex= True, tablefmt='rounded_outline', numalign="right"))"""

        listProperties= []
        for property in deviceChosen.getProperties():
            group= deviceChosen.getPropertyByName(property).getGroup()

            listProperties.append([group, property])

        if 'CONNECTION' in serverConection.getDeviceByName(device).getProperties():
            isON= serverConection.getDeviceByName(device).getPropertyByName('CONNECTION').getElementByName('CONNECTED').getValue()
            if isON == 'On':
                listProperties.append(["BLOB", "Enable BLOB"])
        
        
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

        if property == "Enable BLOB":
            serverConection.enableBLOB(device,'CCD_IMAGE')
        else:
            propertyChosen= deviceChosen.getPropertyByName(property)
            propertyType= propertyChosen.getPropertyType()
            propertyRule= propertyChosen.getRule()
            #propertyPath= propertyChosen.getPath()

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
                d = {key: "Off" for key, value in d.items()}
                d[element]= "On"

            if propertyType == "Number":
                d[element]= input("\nChoose a new value for " + element + ": ") or "0"

            if propertyType == "Text":
                d[element]= input("\nType new text for " + element + ": ") or ""

            propertyChosen.sendValues(d)
            #propertyChosen.sendValues({"TRACE":"On", "ERROR":"On"})

    serverConection.disconnect()