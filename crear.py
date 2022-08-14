import xmpp

username = 'username'
passwd = 'password'
to='name@example.com'
msg='hola'


client = xmpp.Client('alumchat.fun')
client.connect(server=('talk.google.com',5223))
client.auth(username, passwd, 'asd')
client.sendInitPresence()
message = xmpp.Message(to, msg)
message.setAttr('type', 'chat')
client.send(message)