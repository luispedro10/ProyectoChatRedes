import asyncio
import logging
import slixmpp
import aiodns
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream.stanzabase import ET, ElementBase 
import base64, time
from getpass import getpass
from argparse import ArgumentParser
import threading




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
            
            