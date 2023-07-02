import socket
import threading
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import random
import sys
from tabulate import tabulate
tabulate.PRESERVE_WHITESPACE = True
import os
import signal
from colorama import Back, Fore
import requests
import matplotlib.pyplot as plt
import astropy.io.fits as ft
import numpy as np

class INDIGODevice:
    """This is a class representation of a device in the INDIGO protocol.

    :ivar name: Name of the device.
    :ivar server: Instance of the server.
    :ivar properties: List of all properties that are part of the current device.
    """       
    name= None
    server= None
    properties= None

    def __init__(self, name, server):
        self.name= name
        self.server= server
        self.properties= {}

    def _parseVectorTag(self, tag):
        """Here we create the new devices saving its INDIGO elements by instantiating an INDIGOProperty and calling its _parserVectorTag method.

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """
        name= tag.attrib['name']

        if (not name in self.properties):
            self.properties[name] = INDIGOProperty(tag, self)

        self.properties[name]._parseVectorTag(tag)


    def _parseDelTag(self, tag):
        """Here, we delete the property upon receiving a delProperty message from the server.

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """        
        if "name" in tag.attrib:
            name = tag.attrib['name']
            
            if (name in self.properties):

                del self.properties[name]

        else:   # Remove all properties
            #print(self.properties)
                
            self.properties.clear()
        
    def getName(self):
        return self.name
        
    def getPropertyByName(self, name):
        return self.properties[name]
    
    def getProperties(self):
        return self.properties


class INDIGOProperty:
    """This is a class representation of a property in the INDIGO protocol.

    :ivar name: Name of the property.
    :ivar device: Instance of the device that is part of the property.
    :ivar attributes: List of all attributes that the current property has.
    :ivar elements: List of all elements that are part of the current property.
    :ivar lastUpdate: It's a variable that indicates the last time the property was updated.
    """  
    name= None
    device= None
    propertyType= None
    attributes= None
    elements= None
    lastUpdate= 0

    def __init__(self, tag, device):
        self.device= device
        self.name= tag.attrib['name']

        if ("Text" in tag.tag):
            self.propertyType = "Text"
        elif ("Number" in tag.tag):
            self.propertyType = "Number"
        elif ("Switch" in tag.tag):
            self.propertyType = "Switch"
        elif ("Light" in tag.tag):
            self.propertyType = "Light"
        elif ("BLOB" in tag.tag):
            self.propertyType = "BLOB"

        self.attributes= {}
        self.elements= {}

    def _parseVectorTag(self, tag):
        """Here we create the new properties saving its attributes and its INDIGO elements by instantiating an INDIGOElement and calling 
        its _parserElementTag method.

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """
        self.lastUpdate = time.time()

        self.attributes = {**self.attributes, **tag.attrib}     # Merge properties
        
        for elem in tag.findall("./"):
            if (not elem.attrib['name'] in self.elements):
                self.elements[elem.attrib['name']] = INDIGOElement(elem, self)
                
            self.elements[elem.attrib['name']]._parseElementTag(elem)
            
    def getGroup(self):
        if ('group' in self.attributes):
            return self.attributes['group']
        
        return None
    
    def getLabel(self):
        if ('label' in self.attributes):
            return self.attributes['label']
        
        return None
    
    def getPerm(self):
        if ('label' in self.attributes):
            return self.attributes['perm']
        
        return None
    
    def getState(self):
        if ('state' in self.attributes):
            return self.attributes['state']
        
        return None
    
    def getRule(self):
        if ('rule' in self.attributes):
            return self.attributes['rule']
        
        return None
    
    
    def getTimeout(self):
        if ('timeout' in self.attributes):
            return self.attributes['timeout']
        
        return None
    
    def getTimestamp(self):
        if ('timestamp' in self.attributes):
            return self.attributes['timestamp']
        
        return None
    
    def getMessage(self):
        if ('message' in self.attributes):
            return self.attributes['message']
        
        return None
    
    def getLight(self):
        if self.propertyType == "Light":
            print("It's type light")
            print(self.attributes)
            #return self.attributes['light']
    
    def getElementByName(self, name):
        return self.elements[name]
    
    def getPropertyType(self):
        return self.propertyType
    
    def getPropertyName(self):
        return self.name
    
    def getAttributes(self):
        return self.attributes
    
    def getElements(self):
        return self.elements
    
    def getDevice(self):
        return self.device
    
    def sendValues(self, elementNamesAndValues):
        """Function that sends the values to the server, but first applies a filter to send only the correct values and returns an error 
        in case they are wrong.

        :param elementNamesAndValues: Dictionary of the names of elements and its values.
        :type elementNamesAndValues: dict
        """
        sendMessage= True
        rule= self.getRule()
        perm= self.getPerm()

        message = f'<new{self.propertyType}Vector device="{self.device.name}" name="{self.name}">\n'

        if self.propertyType == "Switch":
            numberOfON= 0

            for name, value in elementNamesAndValues.items():
                if value == "On":
                    numberOfON+=1

                message = message + f'  <one{self.propertyType} name="{name}" target="{value}">{value}</one{self.propertyType}>\n'

            if rule == 'OneOfMany':
                if numberOfON != 1:
                    print(Fore.RED + "\n\t\t***** ERROR: You must to select only one element *****\n" + Fore.RESET)
                    sendMessage= False
                    
            elif rule == 'AtMostOne':
                if numberOfON > 1:
                    print(Fore.RED + "\n\t\t***** ERROR: You must to select one or none element *****\n" + Fore.RESET)
                    sendMessage= False

        elif self.propertyType == "Text":
            if perm == "ro":
                print(Fore.RED + "\n\t\t***** ERROR: You can only read this element *****\n" + Fore.RESET)
                sendMessage= False
            elif perm == "wo":
                for name, value in elementNamesAndValues.items():
                    message = message + f'  <one{self.propertyType} name="{name}" target="{value}">{value}</one{self.propertyType}>\n'
            elif perm == "rw":
                for name, value in elementNamesAndValues.items():
                    message = message + f'  <one{self.propertyType} name="{name}" target="{value}">{value}</one{self.propertyType}>\n'
            
        elif self.propertyType == "Number":
            for name, value in elementNamesAndValues.items():
                element= self.getElementByName(name)
                format= element.getFormat()
                step= element.getStep()

                valMin= float(element.getMin())
                valMax= float(element.getMax())
                value= float(value)

                message = message + f'  <one{self.propertyType} name="{name}" target="{value}">{value}</one{self.propertyType}>\n'

                if type(value) != type(valMin):
                    print("\n\t\t***** ERROR: Value is not the right type *****\n")
                    sendMessage= False

                elif (value < valMin) or (value > valMax):
                    print("\n\t\t***** ERROR: Value out of range *****\n")
                    sendMessage= False
            
        elif self.propertyType ==  "BLOB":
            # We downloaded all the images that we have in the server
            for name, value in elementNamesAndValues.items():
                self.device.server.downloadImage(value)
            
        message = message + f'</new{self.propertyType}Vector>\n'

        if sendMessage:
            self.device.server._send(message)



class INDIGOElement:
    """This is a class representation of a elements of properties in the INDIGO protocol.

    :ivar name: Name of the element.
    :ivar prop: Name of the property that the element takes part in.
    :ivar attributes: List of all attributes that the current element has.
    :ivar value: Value tha the element has.
    """
    name = None
    prop = None
    attributes = None
    value = None
    
    def __init__(self, tag, prop):
        self.prop = prop
        self.name = tag.attrib['name']
        self.attributes = {}
        self.value = None
        
    def _parseElementTag(self, tag):
        """Here we create the new elements and save all the attributes and values of the INDIGO elements.

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """
        self.attributes = {**self.attributes, **tag.attrib}    # Merge properties
        self.value = tag.text

        
    def getName(self):
        return self.name
    
    def getLabel(self):
        if ('label' in self.attributes):
            return self.attributes['label']
        
        return None
    
    def getFormat(self):
        if ('format' in self.attributes):
            return self.attributes['format']
        
        return None
    
    def getMin(self):
        if ('min' in self.attributes):
            return self.attributes['min']
        
        return None
    
    def getMax(self):
        if ('max' in self.attributes):
            return self.attributes['max']
        
        return None
    
    def getStep(self):
        if ('step' in self.attributes):
            return self.attributes['step']
        
        return None

    def getPath(self):
        if ('path' in self.attributes):
            return self.attributes['path']

        return None
    
    def getTarget(self):
        if('target' in self.attributes):
            return self.attributes['target']
        
        return None

    def getValue(self):
        return self.value
    
    def getAttributesElement(self):
        return self.attributes
    
    def setValue(self, value):
        """Set a new value to the element.

        :param value: New value to set.
        :type value: float or str
        """        
        self.value= value



class INDIGOServerConnection:
    """This is a class that represents a Server and has all the tools for the connection and management of it.

    :ivar name: Name of the server.
    :ivar _host: IP address of the server.
    :ivar _port: Port for listener of the server. In INDIGO the default port is 7624.
    :ivar _sock: This is a variable that will contain a socket connection to the server.
    :ivar _endReading: Check if the socket has reached the end of reading for the pipeline of the server connection.
    :ivar _thread: This is a variable that will contain a thread that executes a _readerFunction concurrently with the main function.
    :ivar devices: A list of all devices of the server.
    :ivar wait: Set a time to wait to execute some functions.
    :ivar blobMode: It indicate if the BLOB mode is *Never* or *URL*.
    :ivar propertyListeners: List of listeners for properties.
    :ivar messageListeners: List of listeners for messages.
    :ivar serverListener: List of listeners for the server.

    """     
    name= None
    _host= None
    _port = -1
    _sock = None
    _endReading = False
    _thread = None
    devices = None
    wait= 0.5
    blobMode= None

    propertyListeners= None
    messageListeners= None
    serverListener= None

    def __init__(self, name, host, port):
        self.name= name
        self._host= host
        self._port= port
        self._sock= None
        self.blobMode= "NEVER"

        self.devices= {}
        self.propertyListeners= {}
        self.messageListeners= {}
        self.serverListener= {}

    def connect(self):
        """In this function we create a connection with the server using a socket connection. Also, we launch a thread with the execution of 
        _readerFunction to read all messages that the server sends every time. And finally, send a message to the server to get all the 
        properties that it has.
        """        
        try:
            self._sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create the socket and connect to server
            self._sock.connect((self._host, self._port))
            self._sock.settimeout(.01)

        except Exception as err:
            self._sock= None

        if self._sock != None:
            # Create a thread that is reading every time the messages from the server
            _thread= threading.Thread(target=self._readerFunction, daemon= True)
            _thread.start()
        else:
            print("No connection")

        self.sendGetProperties()


    def addServerListener(self, listener):
        """With this function we can add some listeners to the server.

        :param listener: Variable with a function that has the code of what we want the listener to do.
        :type listener: function
        """
        name= self.name
        if not (name in self.serverListener):
            self.serverListener[name]= []

        self.serverListener[name].append(listener)


    def addPropertyListener(self, deviceName, propertyName, listener):
        """In this case we can add some listeners to the property that we want.

        :param deviceName: Name of the device where the property is.
        :type deviceName: str
        :param propertyName: Name of the property that we want to add the listener.
        :type propertyName: str
        :param listener: Variable with a function that has the code of what we want the listener to do.
        :type listener: function
        """
        name= deviceName + "@" + propertyName

        if not (name in self.propertyListeners):
            self.propertyListeners[name]= []

        self.propertyListeners[name].append(listener)

    def addMessageListener(self, deviceName, listener):
        """With this function we can add some listeners to the messages received that we want.

        :param deviceName: Name of the device.
        :type deviceName: str
        :param listener: Variable with a function that has the code of what we want the listener to do.
        :type listener: function
        """        
        name= deviceName

        if not (name in self.messageListeners):
            self.messageListeners[name]= []

        self.propertyListeners[name].append(listener)

    def enableBLOB(self):
        """To take photos and get them, we need to activate the BLOBs on the server. This function changes the value of BLOB to *URL*, 
        since this value is *NEVER* by default.
        """        
        #CCD Imager Simulator       CCD_IMAGE
        blob= self.blobMode

        if blob == "NEVER":
            self.blobMode= "URL"
        else:
            self.blobMode= "NEVER"


    def sendBLOBMessage(self, device, property):
        """This function sends a message to the server to enable the BLOB for a specific property. To do this, the property must be of 
        BLOB type. You must call this function if you want to enable BLOB correctly, as the enableBLOB function doesn't work on its own.

        :param device: Name of the device where the property is.
        :type device: str
        :param property: Name of the property that will have enabled or disabled the BLOB.
        :type property: str.
        """
        if self.blobMode == "URL":
            prop= self.getPropertyByName(device, property)
            if prop.getPropertyType() == "BLOB":
                message= f"<enableBLOB device='{device}' name='{property}'>{self.blobMode}</enableBLOB>"

                print(message)

                self._send(message)

    def getBLOBmode(self):
        return self.blobMode

    def getPropertyByName(self, deviceName, propertyName):
        """With this function, we can obtain property objet from the name of a property.

        :param deviceName: Name of the device for which we want to search for the property.
        :type deviceName: str
        :param propertyName: Name of the property.
        :type propertyName: str
        :return: The objet of the property.
        :rtype: INDIGOProperty
        """
        if (deviceName in self.devices):
            d = self.devices[deviceName]

            if (propertyName in d.properties):
                p = d.properties[propertyName]

                return p

        return None
        
    def isConnected(self):
        """Check if server is connected.

        :return: True if server is connected.
        :rtype: bool
        """        
        if(self._sock != None):
            return True
        
        return False
        
    
    def disconnect(self, _error = None):
        """Disconnect from the server and show an error message if this disconnection is due to an error.

        :param _error: Text of the error, defaults to None
        :type _error: str, optional
        """        
        if (self._sock != None):
            self._endReading = True

            time.sleep(0.3)

            self._sock.close()
            self._sock = None

            if _error:
                print(_error)
    
    def _readerFunction(self):
        """In this function, we read all messages from the server and call some functions that implement the parser in each case. This is
        an infinte loop that only finish when the socket is closed.
        """        
        parser= ET.XMLPullParser(['end'])

        parser.feed("<xml>\n")

        while(not self._endReading) and (not self.is_socket_closed()):
            msg= ""

            try:
                msg= self._sock.recv(500000).decode("UTF-8")
            except Exception as e:
                pass

            if(msg != ""):
                parser.feed(msg)

                for event, elem in parser.read_events():
                    if elem.tag == "defLightVector":
                        print("This a light")
                    if (elem.tag == "defTextVector") or (elem.tag == "defNumberVector") or (elem.tag == "defSwitchVector") or (elem.tag == "defLightVector") or (elem.tag == "defBLOBVector") or (elem.tag == "setTextVector") or (elem.tag == "setNumberVector") or (elem.tag == "setSwitchVector") or (elem.tag == "setLightVector") or (elem.tag == "setBLOBVector"):
                        self._parseVectorTag(elem)
                    elif(elem.tag == "delProperty"):
                        deviceName = elem.attrib['device']
                        self.getDeviceByName(deviceName)._parseDelTag(elem)
                    elif(elem.tag == "message"):
                        print(elem)
                        self._parserMessageTag()
                        
        
        if(self.is_socket_closed()):
            # Call a function with the execute of server's listener  
            if(self.name in self.serverListener):
                for l in self.serverListener[self.name]:
                    l()

            self.disconnect(_error = "Error reading from socket")

    
    def is_socket_closed(self) -> bool:
        """In this function check if the socket is closed.

        :return: True if socket is closed.
        :rtype: bool
        """        
        sock = self._sock
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = sock.recv(16, socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            return False
        return False
    
    def getDevices(self):
        return self.devices
    
    def getDeviceByName(self, device):
        """Obtain the device objet from the name of a device.

        :param device: Name of the device.
        :type device: str
        :return: The objet of the device.
        :rtype: INDIGODevice
        """        
        return self.devices[device]
    
    def getProperties(self, device):
        return device.getProperties()
    
    def getAttributes(self, property):
        return property.getAttributes()
    
    def getElements(self, property):
        return property.getElements()
    
    def getAttributesElement(self, element):
        return element.getAttributesElement()
    
    def downloadImage(self,path):
        """We create a URL with the path in the parameter, the IP of the host, and the port. Later, we check if the downloaded path exists,
        and if it doesn't exist, we create it. Then we save the image file on the client device and show the image.

        :param path: Path of the image file in the server.
        :type path: str
        """        
        # If path is definied
        if path:
            url= "http://" + self._host + ":" + str(self._port) + path

            print(url)

            nameImage= path.split("/")[-1]

            downloadPath= os.getcwd() + "/images"

            if os.path.exists(downloadPath):
                downloadPath= downloadPath + "/" + nameImage
            else:
                os.mkdir(downloadPath)
                downloadPath= downloadPath + "/" + nameImage
            
            r = requests.get(url)
            with open(downloadPath, 'wb') as f:
                f.write(r.content)

            img= ft.open(downloadPath)
            imgData= img[0].data

            plt.imshow(imgData)

            plt.show()

    def _parserMessageTag(self, tag):
        """_summary_

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """        
        deviceName= tag.attrib['device']
        timestamp= tag.attrib['timestamp']

        print(deviceName)

        message= tag.attrib['message']

        if not deviceName in self.devices:
            self.devices[deviceName]= INDIGODevice(deviceName, self)

        self.devices[deviceName]._parseVectorTag(tag)

        print(message)


    def _parseVectorTag(self, tag):
        """Here we create the new elements by instantiating an INDIGODevice and calling its _parserVectorTag method. Finally, we get 
        the name of the device and the name of the property to check if it is in the list of listeners and execute its listener.

        :param tag: Element of the parser of XML message.
        :type tag: xml.etree.ElementTree.Element
        """
        deviceName = tag.attrib['device']

        if not deviceName in self.devices:
            self.devices[deviceName] = INDIGODevice(deviceName, self)

        self.devices[deviceName]._parseVectorTag(tag)

        
        propertyName= tag.attrib['name']

        prop = self.devices[deviceName].getPropertyByName(propertyName)

        name= deviceName + "@" + propertyName

        if(name in self.propertyListeners):
            for l in self.propertyListeners[name]:
                l(prop)


    def _send(self, command):
        """This function is used to send messages to the server whenever needed. This message can be used to turn on or off some devices; 
        create, modify or erase some property, etc

        :param command: Message to send.
        :type command: str
        """        
        command = command.encode("ASCII")

        if(self._sock != None):
            self._sock.sendall(command)


    def sendGetProperties(self):
        """This function is used to get all the things that the server has. The server sends everything in a message and this is read by 
        the _readerFunction, and with this we can complete our client with all devices, properties, elements, etc.
        """        
        self._send('<getProperties version="2.0" />')