import asyncio
import sys
import logging
import slixmpp
import aiodns
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream.stanzabase import ET, ElementBase 
import base64, time
from getpass import getpass
from argparse import ArgumentParser
import threading

#Referencias
#https://github.com/fritzy/SleekXMPP
#https://github.com/poezio/slixmpp/


#Not Implemented Error
if sys.platform == 'win32' and sys.version_info >= (3, 8):
     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Referencia 
#https://github.com/poezio/slixmpp/blob/master/examples/register_account.py
class Registrar(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("register", self.register)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        self.disconnect()

    async def register(self, iq):
        response = self.Iq()
        response['type'] = 'set'
        response['register']['username'] = self.boundjid.user
        response['register']['password'] = self.password

        try:
            await response.send()
            logging.info("Se creo la cuenta", self.boundjid,"\n")
            
        except IqError as e:
            logging.error("Error al registrar ", e,"\n")
            self.disconnect()
            
        except IqTimeout:
            logging.error("Se perdio la conexion")
            self.disconnect()


#ELIMINAR usuario 
# https://github.com/fritzy/SleekXMPP/blob/cc1d470397de768ffcc41d2ed5ac3118d19f09f5/sleekxmpp/plugins/xep_0077/register.py
class Eliminar(slixmpp.ClientXMPP):
    def __init__(self, jid,password):
        slixmpp.ClientXMPP.__init__(self,jid,password)
        self.user=jid
        self.add_event_handler("session_start", self.start)
    
    
    async def start(self,event):
        self.send_presence()
        await self.get_roster()
        borrar = self.Iq()
        borrar['type'] = 'get'
        borrar['from'] = self.boundjid.user
        borrar['password'] = self.password
        borrar['register']['remove'] = 'remove'


        try:
            borrar.send()
            print("Se borro tu cuenta")
            
        except IqError as e:
            print("No se borró la cuenta, error",e)
            self.disconnect()
            
        except IqTimeout:
            print("Se perdio la conexion")
            self.disconnect()


#Mensajeria
#Referencia https://github.com/poezio/slixmpp/blob/master/examples/send_client.py
class Mensaje(slixmpp.ClientXMPP):
     def __init__(self, jid, password, recipient, message):
          slixmpp.ClientXMPP.__init__(self, jid, password)
          self.recipient = recipient
          self.msg = message
          self.add_event_handler("session_start", self.start)
          self.add_event_handler("message", self.message)

     async def start(self, event):
          self.send_presence()
          await self.get_roster()
          self.send_message(mto=self.recipient,mbody=self.msg,mtype='chat')


     def message(self, msg):
          
          if msg['type'] in ('chat'):
          
               recipient = msg['from']
               body = msg['body']
               print(str(recipient) +  ": " + str(body))
               message = input("Mensaje: ")
               self.send_message(mto=self.recipient,mbody=message)

#Mostrar Usuarios
# Referencia https://github.com/poezio/slixmpp/blob/7ddcc3428fbc48814da301ce7cba9b1f855a0fa9/examples/roster_browser.py
class ShowUsers(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("changed_status", self.wait_for_presences)
        self.received = set()
        self.presences_received = asyncio.Event()

    async def start(self, event):
        try:
            await self.get_roster()
        except IqError as err:
            print('Error: %s' % err.iq['error']['condition'])
        except IqTimeout:
            print('Error: Request timed out')
        self.send_presence()


        print('Waiting for presence updates...\n')
        await asyncio.sleep(10)

        print('Roster for %s' % self.boundjid.bare)
        groups = self.client_roster.groups()
        for group in groups:
            print('\n%s' % group)
            print('-' * 72)
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    print(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    print(' %s [%s]' % (jid, sub))

                
                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    print('   - %s (%s)' % (res, show))
                    if pres['status']:
                        print('       %s' % pres['status'])

        self.disconnect()


    
    def wait_for_presences(self, pres):
        self.received.add(pres['from'].bare)
        if len(self.received) >= len(self.client_roster.keys()):
            self.presences_received.set()
        else:
            self.presences_received.clear()




#Mostrar detalles de contacto de un usuario
class UserInfo(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("changed_status", self.wait_for_presences)
        self.received = set()
        self.presences_received = asyncio.Event()

    async def start(self, event):
        try:
            await self.get_roster()
            
        except IqError as err:
            print('Error: %s' % err.iq['error']['condition'])
            
        except IqTimeout:
            print('Error: Request timed out')
        self.send_presence()

        jid_user=input('User jid: ')
        print('Waiting for presence updates...\n')
        await asyncio.sleep(10)

       
        groups = self.client_roster.groups()
        for group in groups:
            print('\n%s' % group)
            print('-' * 72)
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name'] and jid==jid_user:
                    print(' %s (%s) [%s]' % (name, jid, sub))
                    connections = self.client_roster.presence(jid_user)
                    for res, pres in connections.items():
                        show = 'available'
                        if pres['show']:
                            show = pres['show']
                        print('   - %s (%s)' % (res, show))
                        if pres['status']:
                            print('       %s' % pres['status'])
                
                elif self.client_roster[jid]['name']==False and jid==jid_user:
                    print(' %s [%s]' % (jid, sub))
                    connections = self.client_roster.presence(jid_user)
                    for res, pres in connections.items():
                        show = 'available'
                        if pres['show']:
                            show = pres['show']
                        print('   - %s (%s)' % (res, show))
                        if pres['status']:
                            print('       %s' % pres['status'])
        self.disconnect()

    def wait_for_presences(self, pres):
        self.received.add(pres['from'].bare)
        if len(self.received) >= len(self.client_roster.keys()):
            self.presences_received.set()
        else:
            self.presences_received.clear()
   
   
#Cambiar Presencia
class Presence(slixmpp.ClientXMPP):
    def __init__(self, jid,password,option,message):
        slixmpp.ClientXMPP.__init__(self,jid,password)
        self.option=option
        self.message=message
        self.add_event_handler("session_start", self.start)

    async def start(self,event):
        self.send_presence(pshow=self.option,pstatus=self.message)
        await asyncio.sleep(10)
        self.get_roster()
        self.disconnect()
          
          
#Agregar contactos
class Agregar(slixmpp.ClientXMPP):
    def __init__(self, jid, password, to):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.to = to

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        try:
            self.send_presence_subscription(pto=self.to) 
        except IqTimeout:
            print("Se perdio la conexion") 
        self.disconnect()  


        
#Chat grupal
#Referencia https://github.com/poezio/slixmpp/blob/master/examples/muc.py
class GrupoChat(slixmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.jid = jid
        self.room = room
        self.nick = nick
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)

    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room, self.nick) 
        message = input("Mensaje: ")
        self.send_message(mto=self.room, mbody=message, mtype='groupchat')

    def muc_message(self, msg):
        if(str(msg['from']).split('/')[1]!=self.nick):
            print(str(msg['from']).split('/')[1] + ": " + msg['body'])
            message = input("Mensaje: ")
            self.send_message(mto=msg['from'].bare, mbody=message, mtype='groupchat')
    
    
#Enviar recibir archivos 
class Archivos(slixmpp.ClientXMPP):
    def __init__(self, jid, password, receiver, filename):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.receiver = receiver
        self.file = filename
        self.add_event_handler("session_start", self.start)

    async def start(self, event):
        with open (self.file,'rb') as img:
            file_=base64.b64encode(img.read()).decode('utf-8')
            self.disconnect()
        try:
            self.send_message(mto=self.receiver, mbody=file_, mtype='chat')
            print('Sent file ')
            self.disconnect()
        except:
            print('Error sending file')
            self.disconnect()        
      


#Notificaciones      
class Notificacion(slixmpp.ClientXMPP):

    def __init__(self, jid, password, user, message, type_):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.message = message
        self.user = user
        self.type_ = type_

    async def start(self, event):
        
        self.send_presence()
        await self.get_roster()

     
        self.notification_(self.user, self.message, 'active')

    def notification_(self, to, body, my_type):
        
        message = self.Message()
        message['to'] = to
        message['type'] = self.type_
        message['body'] = body

        if (my_type == 'active'):
            fragmentStanza = ET.fromstring("<active xmlns='http://jabber.org/protocol/chatstates'/>")
        elif (my_type == 'composing'):
            fragmentStanza = ET.fromstring("<composing xmlns='http://jabber.org/protocol/chatstates'/>")
        elif (my_type == 'inactive'):
            fragmentStanza = ET.fromstring("<inactive xmlns='http://jabber.org/protocol/chatstates'/>")
        message.append(fragmentStanza)

        try:
            message.send()
        except IqError as e:
            print("Error", e)
        except IqTimeout:
            print("Timeout")

    def message(self, msg):
        recipient = msg['from']
        body = msg['body']
        print(str(recipient) +  ": " + str(body))




#MAIN

print("Implementacion XMPP")
print("----------------------------------")
print("")
print("")
print("1. Iniciar Sesión")
print("2. Registrarse")
print("3.Salir")
print("")
print("")
op = input("Escoja una opcion!: ")
print("----------------------------------")
print("")


usuario = " "
contra = " "        

while (op != "3"):
     
     if(op== "1"):
          usuario = input("Ingrese usuario [Debe ser e.g. pepito@alumchat.fun]: ")
          contra = getpass("Ingrese contraseña: ")
    
    
     elif(op == "2"):
          usuario = input("Ingrese nuevo usuario [Debe ser e.g. pepito@alumchat.fun]: ")
          contra = getpass("Ingrese contraseña: ")
          xmpp = Registrar(usuario, contra)
          xmpp.register_plugin('xep_0030') 
          xmpp.register_plugin('xep_0004') 
          xmpp.register_plugin('xep_0066') 
          xmpp.register_plugin('xep_0077')
          xmpp['xep_0077'].force_registration = True 
          xmpp.connect()
          xmpp.process(forever=False)
          print("Registro Completado\n")
     else:
          print("Ingrese un numero valido")
          
     
     print("")
     print("----------------------------------")
     print("1. Mostrar contactos")
     print("2. Agregar Usuario a contactos")
     print("3. Mostrar detalles de contacto")
     print("4. Comunicacion 1 a 1 con cualquier usuario")
     print("5. Entrar a chat grupal")
     print("6. Cambiar mensaje de presencia")
     print("7. Recibir o enviar archivos")
     print("8. Enviar notificaciones o recibir")
     print("9. Eliminar Cuenta")
     print("10. Cerrar Sesión")
     print("----------------------------------")
     print("")   
     op2  = input("Escoja una opcion!:")
     
     while(op2 != "10"):
          if(op2 =="1"):
               xmpp = ShowUsers(usuario, contra)
               xmpp.register_plugin('xep_0030') # Service Discovery
               xmpp.register_plugin('xep_0199') # Data Forms
               xmpp.register_plugin('xep_0045') # Band Data
               xmpp.register_plugin('xep_0096') # Band Registration
               xmpp.connect()
               xmpp.process(forever=False)
          
          
          elif(op2 == "2"):
               contacto1 = input("Ingrese el nombre del usuario ") 
               xmpp = Agregar(usuario, contra, contacto1)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0199') 
               xmpp.register_plugin('xep_0045') 
               xmpp.register_plugin('xep_0096')  
               xmpp.connect()
               xmpp.process(forever=False)

          
          
          elif(op2 == "3"):
               contacto = input("Escriba el Usuario del contacto: ") 
               xmpp = UserInfo(usuario, contra, contacto)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0199') 
               xmpp.register_plugin('xep_0045') 
               xmpp.register_plugin('xep_0096') 
               xmpp.connect()
               xmpp.process(forever=False)

          
          
          elif(op2 == "4"):
               try:
                    cont = input("Ingrese el usuario quien recibe el mensaje:  ") 
                    msg = input("Mensaje: ")
                    xmpp = Mensaje(usuario, contra, cont, msg)
                    xmpp.register_plugin('xep_0030') 
                    xmpp.register_plugin('xep_0199')
                    xmpp.register_plugin('xep_0045') 
                    xmpp.register_plugin('xep_0096') 
                    xmpp.connect()
                    xmpp.process(forever=False)
               except KeyboardInterrupt as e:
                    print('Se finalizo!')
                    xmpp.disconnect()
         
         
          elif(op2 == "5"):
               try:
                    gr = input("JID del grupo?: ") 
                    nom = input("Ingrese su alias en grupo ")
                    if '@conference.alumchat.fun' in gr:
                         xmpp = GrupoChat(usuario, contra, gr, nom)
                         xmpp.register_plugin('xep_0030')
                         xmpp.register_plugin('xep_0045')
                         xmpp.register_plugin('xep_0199')
                         xmpp.connect()
                         xmpp.process(forever=False)
               except KeyboardInterrupt as e:
                    print('Chat Grupal Finalizado')
                    xmpp.disconnect()
                    
          
          elif(op2 == "6"):
               msg = input("Ingrese su mensaje de presencia: ") 
               xmpp = Presence(usuario, contra, show=False, message=msg)
               xmpp.register_plugin('xep_0030') # Service Discovery
               xmpp.register_plugin('xep_0199') # XMPP Ping
               xmpp.register_plugin('xep_0045') # Mulit-User Chat (MUC)
               xmpp.register_plugin('xep_0096') # Jabber Search
               xmpp.connect()
               xmpp.process(forever=False)
               
          
          elif(op2 == "7"):
               para = input("Ingrese el usuario quien recibe el archivo: ") 
               file = input("Direccion del archivo: ") 
               xmpp = Archivos(usuario, contra, para, file)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0065') 
               xmpp.connect()
               xmpp.process(forever=False)

          
          
          elif(op2 == "8"):
               try:   
                    para = input("Ingrese el usuario quien recibe la notificacion: ") 
                    msg = input("Mensaje: ")
                    ty = input("Tipo: ")
                    xmpp = Notificacion(usuario, contra, para, msg, ty)
                    xmpp.register_plugin('xep_0030')
                    xmpp.register_plugin('xep_0199') 
                    xmpp.register_plugin('xep_0045') 
                    xmpp.register_plugin('xep_0096') 
                    xmpp.connect()
                    xmpp.process(forever=False)
                    
               except KeyboardInterrupt as e:
                    print(' ')
                    xmpp.disconnect()
                    
          
          elif(op2 == "9"):
               xmpp = Eliminar(usuario, contra)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0004') 
               xmpp.register_plugin('xep_0066') 
               xmpp.register_plugin('xep_0077') 
               xmpp.connect()
               xmpp.process()
               xmpp = None
               control = False
               break


          else:
               print("Ingrese un numero valido")


print("adios")