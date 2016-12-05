# Database Table Structure

## Table description

The database structure for our project is really extremely simple and consists of two tables.

### Messages

First we have the main table, called `messages`.

| Field    |  Type         | Key specs        |
| :------- | :-----------  | :--------------- |
| id       | INT           | PRIMARY KEY      |
| from     | VARCHAR(20)   | NOT NULL         |
| to       | VARCHAR(20)   | NOT NULL         |
| reply_to | INT           | FOREIGN KEY (id) |
| subject  | VARCHAR(140)  | NOT NULL         |
| body     | VARCHAR(500)  | NOT NULL         |
| created  | TIMESTAMP     | NOT NULL         |
| read     | INT(1)/BOOL   | NN/DEFAULT 0     |
| priority | CHAR(1) L/M/H | NN/DEFAULT "M"   |

We may choose to add a database check that the `priority` field always has one of the values L/M/H, and that the `read` field always has the value 0 or 1.

### Tags

We also have a simple table called `tags` that attaches tags to messages.

| Field    | Type         | Key specs             |
| :------- | :----------- | :-------------------- |
| msg_id   | INT          | PK, FK (messages.id)  |
| tag      | VARCHAR(20)  | PK                    |
