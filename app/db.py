# Sets up database
from sqlalchemy import *
from datetime import datetime

class Db:

   def __init__(self, config):
      engineName = ''.join(['mysql+mysqlconnector://',
         config['USERNAME'], ':', config['PASSWORD'], '@',
         config['SERVER'], '/', config['SCHEMA']])
      self.engine = create_engine(engineName)
      self.set_metadata()

   def set_metadata(self):
      self.metadata = MetaData(bind=self.engine)

      self.users = Table('users', self.metadata,
         Column('id', Integer, primary_key = True, autoincrement = True),
         Column('email', String(40), ForeignKey('msg_messages.from'), nullable = False),
         Column('name', String(20), nullable = False),
         Column('password', String(20), nullable = False),
      )
      self.messages = Table('msg_messages', self.metadata,
         Column('id', Integer, primary_key = True, autoincrement = True),
         Column('from', String(20), nullable = False),
         Column('to', String(20), nullable = False),
         Column('subject', String(140), nullable = False),
         Column('body', String(5000), nullable = False),
         Column('reply_to', Integer,
            ForeignKey('msg_messages.id'), nullable = True),
         Column('created', DateTime(timezone = True), nullable = False),
         Column('read', Boolean, nullable = False, default = False),
         Column('priority', String(1), nullable = False, default = 'M')
      )
      self.tags = Table('msg_tags', self.metadata,
         Column('msg_id', Integer, ForeignKey('msg_messages.id'),
            primary_key = True),
         Column('tag', String(20), nullable = False, primary_key = True)
      )
      self.metadata.create_all()

   def connect(self):
      return self.engine.connect()

## Will add methods that perform queries here
   ## signup new user
   def add_user(self, email, name, password):
      try:
         conn = self.connect()
         query = insert(self.users).values({'email': email, 'name': name, 'password': password})
         return conn.execute(query)
      except:
         return None
   ## Will create an insert query based on the dictionary m
   def write_message(self, m):
      try:
         conn = self.connect()
         m['created'] = datetime.today()
         if 'read' not in m:
            m['read'] = False
         result = conn.execute(self.messages.insert(), m)
         return result.inserted_primary_key[0]
      except:
         return None

   # Gets all messages based on query
   def get_messages(self, args, username):
     try:
      conn = self.connect()
      query = select([self.messages])
      for field in ['from', 'to']:
         if field in args:
            query = query.where(column(field) == args[field])
      ## Add 'include'
      if args['include'] == 'sent':
         query = query.where(column('from') == username)
      elif args['include'] == 'received':
         query = query.where(column('to') == username)
      else:
         query = query.where(
            or_( column('from') == username, column('to') == username )
         )
      ## Add 'show'
      if args['show'] == 'read':
         query = query.where(column('read') == True)
      elif args['show'] == 'unread':
         query = query.where(column('read') == False)
      ## Add 'order' and direction
      if args['direction'] == 'desc':
         query = query.order_by(column(args['order']).desc())
      else:
         query = query.order_by(column(args['order']))
      ## Perform query
      ##raise ValueError(None)
      return conn.execute(query).fetchall()
     except:
      return None

   # Fetches a single message based on id
   def fetch_message(self, id):
    try: 
      conn = self.connect()
      query = select([self.messages]).where(column('id') == id)
      results = conn.execute(query).fetchall()
      return results[0] if len(results) > 0 else None
    except:
      return False

   # Fetches message tags if any
   def fetch_message_tags(self, id):
    try:
      conn = self.connect()
      query = select([self.tags.c.tag]).where(column('msg_id') == id)
      results = conn.execute(query).fetchall()
      return map((lambda tag: tag[0]), results)
    except:
      return None

   # Inserts a new message/tag pair
   # Should only be called once we have established that the pair does not
   # exist, and that id and tag are valid
   def add_tag(self, id, tag):
      try:
         conn = self.connect()
         result = conn.execute(self.tags.insert(), msg_id=id, tag=tag)
         return result.inserted_primary_key
      except:
         return None

   # Delete a user function
   def delete_user(self, username):
      try:
         conn = self.connect()
         query = delete(self.messages).where(or_(column('from') == username, 
                                                 column('to') == username))
                               
         return conn.execute(query)
      except:
         return None

   # Update read field for a message      
   def update_read(self, id, op):
      try: 
         conn = self.connect() 
         query = update(self.messages).where(column('id') == id).values(read = op)
         return conn.execute(query)    
      except:
         return None

   # Delete a message
   def delete_message(self, id):
      try:
         conn = self.connect() 
         reply_to = update(self.messages).where(column('reply_to') == id).values(reply_to = None)
         conn.execute(reply_to)
         query = delete(self.messages).where(column('id') == id)
         return conn.execute(query)
      except:
         return None
   
   # Delete a tag in a message
   def delete_tag(self, id, tag):
      try:
         conn = self.connect()
         result = delete(self.tags).where(and_(column('msg_id') == id, column('tag') == tag))
         return conn.execute(result)
      except:
         return None

   # Check if tag in the message
   def tag_check(self, id, tag):
      try:
         conn = self.connect()
         query = select([self.tags]).where(and_(column('msg_id') == id, column('tag') == tag))
         results = conn.execute(query).fetchall()
         return True if len(results) > 0 else False
      except:
         return None

   # Check for valid user
   def check_user(self, user):
      try:
         conn = self.connect()
         query = select([self.users]).where(column('email') == user)
         result = conn.execute(query).fetchall()
         return True if len(result) > 0 else False
      except:
         return None

   # Check creditials for login
   def check_login(self, email, password):
      try:
         conn = self.connect()
         query = select([self.users]).where(and_(column('email') == email, column('password') == password))
         result = conn.execute(query).fetchall()
         return True if len(result) > 0 else False
      except:
         return None

   # Get user name
   def get_user_name(self, username):
      try:
         conn = self.connect()
         query = select([self.users.c.name]).where(column('email') == username)
         result = conn.execute(query).fetchall()
         return "Not registered user" if len(result) == 0 else result[0]['name']
      except: 
         return None






