This is the python library for City Hall Enterprise Settings Server

 ABOUT

 This project is written in Python 2.7 and can be installed using:
   pip install cityhall



 USAGE

 The intention is to use the built-in City Hall web site for actual
 settings management, and then use this library for consuming those
 settings, in an application.  As such, there are only a few commands to 
 be familiar with:

 from cityhall import Settings
 
 cityhallSettings = Settings(username, password) - Must be called to 
     initiate a session with City Hall. The password should be in 
     plaintext, it will be hashed by the library.
 
 cityhallSettings.logout() - To be called when the session is over.
 
 cityhallSettings.get() - This should be the way to retrieve a value.
     To get the value of '/some_app/value1', use:
        cityhallSettings.Get('/some_app/value1')

 For more in depth information about this library, please check the wiki.

     