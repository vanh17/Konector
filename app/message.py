# message.py
# Collects methods that handle details of messages

# Checks that the message information in the dictionary m is valid:
# - There should be a `from` with length at most 20
# - There should be a `to` with length at most 20
# - There should be a `subject` with length at most 140
# - There should be a `body` with length at most 5000
def validate_new_message(m):
   for field in ['to', 'subject', 'body']:
      if field not in m:
         return 'Required fields: to, subject, body'
   # if len(m.keys()) > 4:
   #    return 'Only fields allowed: to, subject, body'
   for field, length in [('from', 20), ('to', 20),
                         ('subject', 140), ('body', 5000)]:
      if len(m[field]) > length:
         return 'Field "%s" must not exceed length %d' % (field, length)
   return None

# Checks that a query for a message has proper settings
def validate_message_query(args, username):
   for key in args:
      if key not in ['from', 'to', 'include', 'show', 'order', 'direction']:
         return 'Unknown field: %s' % key
   if (len(username)) > 20:
      return 'Username cannot exceed 20 characters'
   for field in ['from', 'to']:
      if field in args and len(args[field]) > 20:
         return 'Field %s cannot exceed 20 characters' % field
   for key, default in [('include', 'all'), ('show', 'all'), ('order', 'created'), ('direction', 'asc')]:
      if key not in args:
         args[key] = default
   for field, options in [('include', ['sent', 'received', 'all']),
                          ('show', ['read', 'unread', 'all']),
                          ('order', ['created', 'read', 'subject', 'to', 'from']),
                          ('direction', ['asc', 'desc'])]:
      if args[field] not in options:
         return 'Invalid option for %s. Allowed options: ' % (field, ','.join(options))
   return None      
# Checks that the request body to be JSON document with a "read" field 
# value of true or false, and nothing else.
def  validate_request_body(r):
   if 'read' not in r:
      return 'It needs to have a read field'
   if r['read'] not in [True, False]:
      return 'Invalid option for %s. Allowed options: ' % ("read", 'True, False')
   return None