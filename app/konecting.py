## messaging.py
##
## Start the application by running `python3 app/messaging.py`
##
from sqlalchemy import Table, Column, Integer, String
from flask import Flask, make_response, json, url_for, request, redirect
import flask
import re
from db import Db   # See db.py
# import user # See user.py
import konect # See message.py

app = Flask(__name__)
# The keys.json file should contain the 4 properties:
# DATABASE, PASSWORD, SERVER, SCHEMA
app.config.from_json('keys.json')
app.config['DEBUG'] = True  # Turn this to True to enable debugging


## Setting up database
db = Db(app.config)

#######################################
## ROUTES
## Here we specify the different routes

## First time someone visits the site. They should be shown options for creating
## a new user or logging in as a new user
@app.route('/', methods = ['GET'])
def index():
   return flask.render_template('index.html', has_result=False)

@app.route('/search', methods = ['GET'])
def search():
   query = request.args.get('q')
   users = re.findall('(?<=@)[a-zA-Z]+\w+', query)
   tags = re.findall('(?<=#)\w+', query)
   args = request.args.to_dict()
   print(users)
   print(tags)
   print(args)
   results = []
   if len(tags) > 0:
      results = [
         (db.find_konects_with_tag(tag))[0]
         for tag in tags
      ]
   print(results)
   return flask.render_template('index.html', has_result=True, result={'route': 'search_box', 'search': results, 'query': query})

# route for handling the login modal
@app.route('/login', methods = ['POST'])
def login():
  error = None
  if request.method == "POST":
    email = request.form['username']
    password = request.form['password']
    # print(email, ' ', password)
    # print(db.check_login(email, password))
    if db.check_login(email, password):
      return make_json_response({'url': url_for('user_page', username=request.form['username']), 'error': error}, 200)
      #return make_json_response({'user': email, 'pass': password}, 200)
    else:
      error = "Invalid username or password. Please try again"      
  # return flask.render_template('index.html', error=error)
  return make_json_response({'error': error}, 400)

# route for handling the signup modal
# route for handling the login modal
@app.route('/signup', methods = ['POST'])
def signup():
  error = None
  if request.method == "POST":
    email = request.form['username']
    name = request.form['name']
    password = request.form['password']
    if not db.check_user(email):
      if name == "":
        error = "Full name cannot be empty"
        return make_json_response({'error': error}, 400)
      if db.add_user(email, name, password) is not None:
         return make_json_response({'error': error}, 200)
         #return make_json_response({'user': email, 'pass': password}, 200)
      else:
         error = 'Cannot signup. Please try again. Server not available'
         return make_json_response({'error': error}, 500)
    else:
      error = "username is already taken"      
  # return flask.render_template('index.html', error=error)
  return make_json_response({'error': error}, 400)

@app.route('/users/<username>', methods = ['GET'])
def user_page(username):
  result = {
    'route': 'user_page',
    'check': db.check_user(username),
    'user': username,
    'create': {
      'url': url_for('user_new_konect', username=username),
      'content': {'body': '' }
    },
    'tweet': url_for('user_konects', username=username)
  }
  return flask.render_template('index.html', has_result=True, result=result)

## Creates a new user. Request body contains the password to be used
## If user/password exists, must ensure it is same or else throw error
## In first iteration of the app, no passwords.

@app.route('/users/<username>', methods = ['DELETE'])
def user_delete(username):
   if len(username) > 20:
      return make_json_response({ 'error': 'username too long' }, 400)   
   results = db.delete_user(username)
   if results is  None:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)
   return make_json_response({}, 204) ##can return null content no matter what we put at the content 

## Returns information about a user's messages. We should allow complex
## queries here
@app.route('/users/<username>/konects', methods = ['GET'])
def user_konects(username):
   args = request.args.to_dict()
   print(args)
   error = konect.validate_konect_query(args, username)
   if error is not None:
      return make_json_response({ 'error': error }, 400)  
   results = db.get_konects(args, username)
   konects = db.get_konects(args, username)
   print(konects)
   if results is  None:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)
   results = {
      'route': 'user_messages',
      'mentioned': [
         { 'url': url_for('konect_get', id=m['id']),
           'from': db.get_user_name(m['sender']),
           'body': m['body'],
           'created': m['created'].strftime('%d, %b %Y'),
           'read': m['read'],
           'id': m['id']
         } 
         for m in results['mentioned']
      ],
      'sent': [
         { 'url': url_for('konect_get', id=m['id']),
           'from': db.get_user_name(m['sender']),
           'body': m['body'],
           'created': m['created'].strftime('%d, %b %Y'),
           'id': m['id']
         } 
         for m in results['sent']
         if m['sender'] == username
      ]
   }
   return flask.render_template("index.html", has_result=True, result=results)

## Used to post a new message. Body contains information about recipient
## - Validate the message
## - Add to database
@app.route('/users/<username>/konects', methods = ['POST'])
def user_new_konect(username):
   body = request.form['body']
   contents = {}
   if 'reply_to' in request.form:
      contents['reply_to'] = request.form.get('reply_to', type=int)
   #extract the recipents
   mentions = re.findall('(?<=@)[a-zA-Z]+\w+', body)
   tags = re.findall('(?<=#)\w+', body)
   contents['body'] = body
   contents['sender'] = username
   error = konect.validate_new_konect(contents)
   if error is not None:
      return make_json_response({ 'error': error }, 400)
   record_id = db.write_konect(contents)
   print(record_id)
   print(mentions)
   print(tags)
   if record_id is None:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)
   for tag in tags:
      db.add_tag(record_id, tag)
   for mention in mentions:
      db.add_mention(record_id, mention)
   return make_json_response({}, 201, {
      'Location': url_for('konect_get', id=record_id)
   })



## Get a particular message
@app.route('/konect/<id>', methods = ['GET'])
def konect_get(id):
   results = db.fetch_konect(id)
   print(results[0]['id'] + 100)
   if results is None:
      return make_json_response({ 'error': 'Cannot find specified id' }, 404)
   if results is False:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)   
   j_results = [
     {
        "id": m['id'],
        "from": m["sender"],
        "isMain": m['id'] == int(id),
        "reply_to": m["reply_to"],
        "created": m['created'].strftime('%d, %b %Y'),
        "body": m["body"],
     }
     for m in results
   ]
   print(j_results)
   json_response = make_json_response(j_results, 200)
   return flask.render_template('message.html', has_result=True, result=j_results)

## Change a read status of a message
@app.route('/messages/<id>', methods = ['POST'])
def message_mark_read(id):
   r = request.json
   error = message.validate_request_body(r)
   if error is not None:
      return make_json_response({ 'error' : error }, 400)
   op = 1 if r["read"] else 0   
   mExit = db.fetch_message(id)
   if mExit is None:
      return make_json_response({ 'error': 'Can not specify the message' }, 404)
   result = db.update_read(id, op)   
   if result is None:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)
   return make_json_response({}, 204)

## Delete a message
@app.route('/messages/<id>', methods = ['DELETE'])
def message_remove(id):
   mExit = db.fetch_message(id)
   if mExit is None:
      return make_json_response({ 'error': 'Can not specify the message' }, 404)
   result = db.delete_message(id)
   if result is None:
      return make_json_response({ 'error': 'Internal Server Error' }, 500)
   return make_json_response({}, 204)


# ## Get whether a given tag is in place for this message
# @app.route('/messages/<id>/tags/<tag>', methods = ['GET'])
# def tag_check(id, tag):
#    if (len(tag) > 20):
#       return make_json_response({ 'error' : 'tag too long' }, 400)
#    hasMessage = db.fetch_message(id)
#    if hasMessage is None:
#       return make_json_response({ 'error' : 'No message found' }, 404)
#    check = db.tag_check(id, tag)
#    if (hasMessage is False) or (check is None):
#       return make_json_response({ 'error' : 'Internal Server Error' }, 500)
#    if check:
#         return make_json_response({}, 204)
#    return make_json_response({ 'error' : 'No tag in specified message' }, 404)

# ## Adds a tag to a message, if it did not exist
# @app.route('/messages/<id>/tags/<tag>', methods = ['PUT'])
# def tag_add(id, tag):
#    if len(tag) > 20:
#       return make_json_response({ 'error': 'tag too long' }, 400)
#    message = db.fetch_message(id)
#    if message is None:
#       return make_json_response({ 'error': 'message not found' }, 404)
#    tags = db.fetch_message_tags(id)
#    if tag in tags:
#       return make_json_response({}, 204)
#    # Need to add the tag
#    if db.add_tag(id, tag) is None:
#       return make_json_response({ 'error': 'server error' }, 500)
#    return make_json_response({}, 201)

# ## Removes a tag from a message
# @app.route('/messages/<id>/tags/<tag>', methods = ['DELETE'])
# def tag_remove(id, tag):
#    if (len(tag) > 20):
#       return make_json_response({ 'error' : 'tag too long' }, 400)
#    message = db.fetch_message(id)
#    if message is None:
#       return make_json_response({ 'error': 'message not found' }, 404)
#    tagExist = db.tag_check(id, tag)
#    if tagExist is False:
#      return make_json_response({ 'error': 'tag cannot be found' }, 404)
#    result = db.delete_tag(id, tag)
#    if (result is None) or (tagExist is None):
#       return make_json_response({ 'error': 'Internal Server Error' }, 500)
#    return make_json_response({}, 204)


#####################################
## Helper methods go here

## Helper method for creating JSON responses
def make_json_response(content, response = 200, headers = {}):
   headers['Content-Type'] = 'application/json'
   return make_response(json.dumps(content), response, headers)


#####################################

## Starts the application
if __name__ == '__main__':
   app.run()
