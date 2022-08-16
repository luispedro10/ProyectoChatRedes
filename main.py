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

if sys.platform == 'win32' and sys.version_info >= (3, 8):
     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


#Registrar usuario
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

#Lista (Roster)
class Roster(slixmpp.ClientXMPP):
    def __init__(self, jid, password, user=None, show=True, message=""):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.presences = threading.Event()
        self.contacts = []
        self.user = user
        self.show = show
        self.message = message

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

        contactos = []
        try:
            self.get_roster()
            
        except IqError as e:
            print("Error ", e)
            
        except IqTimeout:
            print("Se perdio la conexion")
        
        self.presences.wait(3)


        rosters = self.client_roster.groups()
        for group in rosters:
            for user in rosters[group]:
                status = show = answer = priority = ''
                self.contacts.append(user)
                subs = self.client_roster[user]['subscription']
                conexions = self.client_roster.presence(user)
                username = self.client_roster[user]['name'] 
                for answer, pres in conexions.items():
                    if pres['show']:
                        show = pres['show']
                    if pres['status']:
                        status = pres['status']
                    if pres['priority']:
                        status = pres['priority']


                contactos.append([
                    user,
                    subs,
                    status,
                    username,
                    priority
                ])
                self.contacts = contactos

        if(self.show):
            if(not self.user):
                if len(contactos)==0:
                    print('No hay nadie conectado')
                else:
                    print('Usuarios: \n')
                for contact in contactos:
                    print('\tUsuario:' , contact[0] , '\t\tEstatus:' , contact[2])
            else:
                print('\n\n')
                for contact in contactos:
                    if(contact[0]==self .user):
                        print('\tUsuario:' , contact[0] , '\n\tEstatus:' , contact[2] , '\n\tNombre:' , contact[3])
        else:
            for JID in self.contacts:
                self.notification_(JID, self.message, 'active')

        self.disconnect()

    def notification_(self, to, body, my_type):

        message = self.Message()
        message['to'] = to
        message['type'] = 'chat'
        message['body'] = body

        if (my_type == 'active'):
            stanza = ET.fromstring("<active xmlns='http://jabber.org/protocol/chatstates'/>")
        elif (my_type == 'composing'):
            stanza = ET.fromstring("<composing xmlns='http://jabber.org/protocol/chatstates'/>")
        elif (my_type == 'inactive'):
            stanza = ET.fromstring("<inactive xmlns='http://jabber.org/protocol/chatstates'/>")
        message.append(stanza)

        try:
            message.send()
        except IqError as e:
            print("Error", e)
        except IqTimeout:
            print("Se perdio la conexion")
   

          
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
        self.file = open(filename, 'rb')
        self.add_event_handler("session_start", self.start)

    async def start(self, event):
        try:
            proxy = await self['xep_0065'].handshake(self.receiver)
            while True:
                data = self.file.read(1048576)
                if not data:
                    break
                await proxy.write(data)

            proxy.transport.write_eof()
        except (IqTimeout) as e:
            print('Se perdio la conexion', e)
        else:
            print('Archivo enviado!')
        finally:
            self.file.close()
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
            print("Error ", e)
        except IqTimeout:
            print("Se perdio la conexion'")

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
          usuario = input("Ingrese nuevo usuario: ")
          contra = getpass("Ingrese contraseña: ")
          xmpp = Registrar(usuario, contra)
          xmpp.register_plugin('xep_0030') 
          xmpp.register_plugin('xep_0004') 
          xmpp.register_plugin('xep_0066') 
          xmpp.register_plugin('xep_0077') 
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
               xmpp = Roster(usuario, contra)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0199') 
               xmpp.register_plugin('xep_0045')
               xmpp.register_plugin('xep_0096') 
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
               xmpp = Roster(usuario, contra, contacto)
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
               xmpp = Roster(usuario, contra, show=False, message=msg)
               xmpp.register_plugin('xep_0030') 
               xmpp.register_plugin('xep_0199')
               xmpp.register_plugin('xep_0045') 
               xmpp.register_plugin('xep_0096')
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
