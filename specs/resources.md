# Resources

This document describes the different resources that form this RESTful service, and their URL schema.

There are three main resources at this point:

- A user resource. It is stored in the database along with a password, when a user is created.
    - Base schema: `users/{username}`
    - A GET on this resource returns basic user "links"
    - A PUT on this resource creates a new user. A password needs to be delivered as part of the body.
    - A DELETE on this resource removes the user and all their messages from the system.
- The list of sent and received messages for a given user.
    - Base schema: `users/{user}/messages`
    - A GET on the list fetches all messages, both sent and received. More precisely, it returns links to GET requests for the messages. It also provides instructions for the submission of a new message. It would optionally allow for some query parameters (count, since date, only read/unread, only read or only sent).
    - A POST on the list creates a new message. You must specify a recipient, a subject line and a text body.
    - No PUT/DELETE allowed.
- An individual message, identified via an increasing id.
    - Base schema: `messages/{msg_id}`
    - A GET on the message provides all the information for the message. It also offers a link to reply to the message, as well as links to the various tags for the message.
    - A POST on the message can be used to mark the message as read.
    - A DELETE will delete the message.
    - No PUT allowed.
- A message with a tag attached to it.
    - Base schema: `messages/{msg_id}/tag/{tag}`
    - A GET on such a schema returns 200 or 404 based on whether the tag is associated with the message.
    - A PUT on such a schema associates a specific tag with the specific message.
    - A DELETE on such a schema will remove that tag from the message.
    - No POST allowed.

At this point we are not concerned with permissions questions, but later on we will be.

Here is a tabular representation of the same information:

| Schema                     | GET   | PUT    | POST      | DELETE          |
| :-----------------------   | :---- | :--    | :-------- | :-------------- |
| `users/{user}`             | info  | create | N/A       | delete, cascade |
| `users/{user}/messages`    | list  | N/A    | new msg   | N/A             |
| `messages/{id}`            | view  | N/A    | mark read | delete          |
| `messages/{id}/tags/{tag}` | check | tag    | N/A       | untag           |

## Request specifics

We will now discuss each of these resources and request types in detail, outlining the input and output expected as well as the kinds of possible errors.

All methods return a 500 error in case of problems with database access.

### `GET users/{user}`

- A request to "get" a specific user.
- It requires no other query parameters.
- It should return a JSON with the user's login information and, most importantly, links to other actions for that user.
- Always returns a 200 (unless we create user accounts).

Sample JSON return:
```json
{
    "user": "...",
    "sent": "... link to a GET request for all sent mail ...",
    "received": "... link to a GET request for all received mail ...",
    "unread": {
        "count": "... number of received unread mail ...",
        "url": "... link to a GET request for unread mail ..."
    },
    "create": {
        "url": "... link to POST request for creating new mail ...",
        "content": { "to": "", "subject": "", "body": "" }
    },
    "tags": [
        {
            "tag": "... a tag name that user has used ...",
            "url": "... link to a GET request for all mail with that tag ..."
        }
    ]
}
```

### `PUT users/{user}`

- A request to "create" a specific user.
- Takes no other parameters (until we ask for passwords).
- If the username is too long (over 20 characters), returns 400 with a JSON payload containing an 'error' field.
- Otherwise returns a 201 with a "Location" header pointing to the corresponding GET, and no body.
- Optional: For "existing" users, it should ideally return a 200 or 204.

### `DELETE users/{user}`

- Deletes a user, by removing all messages that the user has sent or received.
- No other parameters.
- Returns 400 as PUT for a long username.
- Otherwise returns a 204.

### `GET users/{user}/messages`

- Returns links to a user's messages. Also contains a "form" for creating a new message.
- Returns a 400 with an error key in the payload for long usernames.
- Returns a 200 otherwise.
- Extra "filter" parameters allowed:
    - "include" with possible values "sent", "received" or "all".
    - "show" with possible values "read", "unread" or "all".
    - "order" with possible values "created", "read", "subject", "to" or "from".
    - "direction" with possible values "asc" or "desc".
    - "to" and "from".
- One important question is how to "provide" the filter parameters to make them discoverable.

Sample JSON return:
```json
{
    "create": {
        "url": "... url for POST request for creating new email",
        "content": { "to": "", "subject": "", "body": "" }
    },
    "messages": [
        { "url": "... url for GET for a specific message ..." },
        {}
    ]
}
```

### `POST users/{user}/messages`

- Creates a new message
- Expects the request body to contain "to", "subject" and "body" fields.
- Issues 400 errors if those are not suitably provided or are too long.
- Returns a 201 code with a "location" header pointing to the new message.

### `GET messages/{id}`

- Returns a specific message
- Returns a 404 error if that message id does not exist
- Returns a 200 response with a JSON payload containing information about the message, as well as a link to "reply".

Sample return JSON:
```json
{
    "id": "... message id ...",
    "from": "... sender ...",
    "to": "... recipient ...",
    "subject": "... subject line ...",
    "body": "... text body ...",
    "read": "... read status true/false ...",
    "tags": [
        {  "url": "... url for the message/tag pair ..." },
        {  "url": "... a second tag ..." }
    ],
    "add_tag": {
        "url": "... url scheme for adding a tag ..."
    }
}
```

### `POST messages/{id}`

- Used for updating a message, specifically the read status.
- Tags are on a separate request.
- Returns 404 if the message id does not exist.
- Returns a 204 on successful update.
- The request body must contain a JSON dictionary with a "read" entry.

### `DELETE messages/{id}`

- Deletes the message.
- Question: What if there have been replies?
    - Must either break the reply link,
    - or must delete those replies as well.
- Returns a 404 if the id doesn't exist.
- Returns a 204 on successful delete.`

### `GET messages/{id}/tags/{tag}`

- Simply reports if the tag exists for this message.
- Returns a 400 if the tag is too long.
- A 404 error if the message id doesn't exist.
- Also a 404 if the message doesn't have that tag.
- A 204 if the message has that tag.

### `PUT messages/{id}/tags/{tag}`

- Adds a tag to the message.
- Returns a 400 error if the tag is too long.
- Returns a 404 error if the id doesn't exist.
- Returns a 201 if the message didnt have this tag before.
- Returns a 204 if the message did have this tag before.

### `DELETE messages/{id}/tags/{tag}`

- Removes a tag from a message.
- Returns a 400 error if the tag is too long.
- Returns a 404 error if the id doesn't exist or if the message doesn't have that tag.
- Returns a 204 on successful removal.
