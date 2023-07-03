####
Demo
####

Here, let’s see a tiny demo to show how to use the INDIGO client library.

Primarily, we have a function that will serve as a listener for a property. This shows a message when one is turned on.

.. code-block:: Python

   def connected(property):
    if(property.getElementByName('CONNECTED').getValue() == 'On'):
        print("The device " + str(property.getDevice().getName()) + " is connected")


First of all, we need to make the connection with the server. So we need to provide the IP address and port of the server.

The default port for INDIGO is 7624.

.. code-block:: Python

    host = "172.30.124.160" # This is an example of IP address
    port = 7624

And now we make a connection to the server by instantiating an INDIGOServerConnection and then we create the connection. The parameters are:

* The name that you want to give to the server. 
* Host.
* Port.

.. code-block:: Python

    serverConnection= INDIGOServerConnection("Server", host, port)
    serverConnection.connect()

It is recommended to allow some time for the client to read all the data from the server.

.. code-block:: Python

    time.sleep(0.5)

Now we have the connection and can make all we want. For example:

We can add a listener to some devices.

.. code-block:: Python

    device= serverConnection.getDevices()

    devices= []
    for deviceName, device in serverConnection.getDevices().items():
        serverConnection.addPropertyListener(deviceName, 'CONNECTION', connected)
        devices.append(device)

We can turn on some device.

We check if the first device in the list has the CONNECTION property. And if true, we send the element CONNECTED to On.

.. code-block:: Python

    if 'CONNECTION' in devices[0].getProperties():
        devices[0].getPropertyByName('CONNECTION').sendValues({"CONNECTED":"On"})

We can enable BLOB obbjets. In this case I use a CCD_IMAGE property, because I know that is a BLOB property.

.. code-block:: Python

    time.sleep(0.5)

    serverConnection.enableBLOB()

    serverConnection.sendBLOBMessage(devices[0].name, 'CCD_IMAGE')

Now we can take a photo with the property CCD_EXPOSURE

.. code-block:: Python
    
    devices[0].getPropertyByName('CCD_EXPOSURE').sendValues({"EXPOSURE":"2"})

We must wait for the time that we indicated in the EXPOSURE above.

.. code-block:: Python

    time.sleep(2.5)

And now we can see the photo with the property CCD_IMAGE

.. code-block:: Python

    devices[0].getPropertyByName('CCD_IMAGE').sendValues({"IMAGE":str(devices[0].getPropertyByName('CCD_IMAGE').getElementByName('IMAGE').getPath())})

The image will be downloaded to a folder named ``images`` and it will be displayed for viewing.

Now we turn off the device and disconnect the client from the server.

.. code-block:: Python

    devices[0].getPropertyByName('CONNECTION').sendValues({"DINCONNECTED":"On"})

    serverConnection.disconnect()


You can see and download the source code `here <https://github.com/Gogilga/INDIGO-Python-Bib/blob/main/project/demo.py>`_.