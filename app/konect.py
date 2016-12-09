# message.py
# Collects methods that handle details of messages

# Checks that the message information in the dictionary m is valid:
# - There should be a `from` with length at most 20
# - There should be a `to` with length at most 20
# - There should be a `subject` with length at most 140
# - There should be a `body` with length at most 5000
def validate_new_konect(m):
   for field in ['sender', 'body']:
      if field not in m:
         return 'Required fields: from, body'
   # if len(m.keys()) > 4:
   #    return 'Only fields allowed: to, subject, body'
   for field, length in [('sender', 20), ('body', 5000)]:
      if len(m[field]) > length:
         return 'Field "%s" must not exceed length %d' % (field, length)
   return None

# Checks that a query for a message has proper settings
def validate_konect_query(args, username):
   for key in args:
      if key not in ['sender', 'to', 'include', 'show', 'order', 'direction']:
         return 'Unknown field: %s' % key
   if (len(username)) > 20:
      return 'Username cannot exceed 20 characters'
   for field in ['sender', 'to']:
      if field in args and len(args[field]) > 20:
         return 'Field %s cannot exceed 20 characters' % field
   for key, default in [('include', 'all'), ('show', 'all'), ('order', 'created'), ('direction', 'asc')]:
      if key not in args:
         args[key] = default
   for field, options in [('include', ['sent', 'mentioned', 'all']),
                          ('show', ['read', 'unread', 'all']),
                          ('order', ['created', 'read']),
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