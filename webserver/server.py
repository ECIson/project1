#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, session, request, render_template, g, redirect, Response
from random import randint

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'

#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
# DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://eci2109:8s6dy@104.196.175.120/postgres"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request

    The variable g is globally accessible
    """
    try:
        g.conn = engine.connect()
    except:
        print "uh oh, problem connecting to database"
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print request.args


    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT username, password FROM users")
    users = {}
    for result in cursor:
        users[result['username']] = result['password']
    cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data = users)


    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
    return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    print name
    cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
    g.conn.execute(text(cmd), name1 = name, name2 = name);
    return redirect('/')


@app.route('/login', methods=["POST", "GET"])
def login():
    username = request.form['uname']
    password = request.form['psw']
    cursor = g.conn.execute("SELECT userid, username, password FROM users")
    for row in cursor:
        if username == row['username']:
            if password == row['password']:
                cursor.close()
                context = dict(data = row['username'])
                # return render_template('user_homepage.html', context)
                return user_homepage(row['userid'])
            else:
                break
    cursor.close()
    return render_template('wrong_login.html')


@app.route('/user_homepage.html')
def user_homepage(user):
    cursor = g.conn.execute("SELECT * FROM users WHERE userid = " + str(user))  # FLAG
    stats = cursor.fetchone()
    context = {}
    context['username'] = stats[1]
    context['rank'] = stats[3]
    context['stars'] = stats[4]
    session['user'] = user
    cursor.close()
    return render_template('user_homepage.html', **context)
    
    
@app.route('/cards')
def cards():
    user = session['user']
    cursor = g.conn.execute("SELECT * FROM users, users_have_cards, cards_and_relations, classes WHERE users.userid = " + str(user) + " AND users.userid=users_have_cards.userid AND users_have_cards.cardid=cards_and_relations.cardid AND classes.classid=cards_and_relations.classid ORDER BY cards_and_relations.name ASC")  # FLAG
    context = {}
    context['cards'] = cursor.fetchall()
    cursor.close()
    return render_template('cards.html', **context)
    
@app.route('/decks')
def decks():
    user = session['user']
    cursor = g.conn.execute("SELECT * FROM users, decks, classes WHERE users.userid = " + str(user) + " AND users.userid=decks.userid AND classes.classid=decks.classid ORDER BY decks.name ASC")  # FLAG
    context = {}
    context['decks'] = cursor.fetchall()
    cursor.close()
    return render_template('decks.html', **context)
    
@app.route('/decks/<id>')
def decks_id(id):
    user = session['user']
    context = {}
    context['cards'] = []
    for n in range(1,30):
      cursor = g.conn.execute("SELECT * FROM users, cards_and_relations, classes, decks WHERE users.userid = " + str(user) + " AND decks.deckid = " + str(id) + " AND users.userid=decks.userid AND " + 
  ''' decks.cardid'''+str(n)+''' = cards_and_relations.cardid AND classes.classid=cards_and_relations.classid ORDER BY cards_and_relations.name ASC''')  # FLAG
      context['cards'].append(cursor.fetchall())

    return render_template('deckcards.html', **context)

    
@app.route('/card_glossary')
def card_glossary():
    cursor = g.conn.execute("SELECT * FROM cards_and_relations, classes WHERE classes.classid=cards_and_relations.classid ORDER BY cards_and_relations.name ASC")  # FLAG
    context = {}
    context['cards'] = cursor.fetchall()
    cursor.close()
    return render_template('card_glossary.html', **context)

@app.route('/store')
def store():
    cursor = g.conn.execute("SELECT * FROM expansions WHERE CAST(startdate AS DATE) < CAST(NOW() AS DATE)") # AND (CAST(enddate AS DATE) > CAST(NOW() AS DATE) OR enddate IS NULL)")
    context = {}
    context['expansions'] = cursor.fetchall()
    cursor.close()
    return render_template('store.html', **context)

@app.route('/inventory')
def inventory():
    cursor = g.conn.execute("SELECT * FROM packs_and_buys INNER JOIN  expansions ON "
                            "packs_and_buys.expansionid = expansions.expansionid WHERE userid = " + str(session['user']))
    context = {}
    context['packs'] = cursor.fetchall()
    cursor.close()
    return render_template('inventory.html', **context)

@app.route('/purchased', methods=["POST", "GET"])
def purchased():
    if session['user'] is None:
        return render_template('sign_in.html')
    else:
        cursor = g.conn.execute("SELECT * FROM packs_and_buys WHERE expansionid = " + request.form['expan'] + " AND userid = " + str(session['user']))
        r = cursor.first()
        if r is None:
            print('A')
            g.conn.execute("INSERT INTO packs_and_buys VALUES(1, 1, " + request.form['expan'] + ", " + str(session['user']) + ")")
            cursor.close()
        else:
            print('B')
            g.conn.execute("UPDATE packs_and_buys SET quantity = quantity + 1 WHERE expansionid = " + request.form['expan'] + " AND userid = " + str(session['user']))
            cursor.close()
        return user_homepage(session['user'])

@app.route('/open', methods=["POST", "GET"])
def open():
    cursor = g.conn.execute("SELECT c.cardid, c.name, c.rarityname, c.expansionid, r.weight FROM cards_and_relations "
                            "AS c INNER JOIN raritytable AS r ON c.rarityname = r.name WHERE c.expansionid = " + request.form['pack'])
    r = cursor.fetchall()
    if r is None:
        cursor.close()
        return render_template("pack_empty.html")
    else:
        cards = chooseFive(r)
        context = {}
        context['cards'] = cards
        for card in cards:
            cursor2 = g.conn.execute("SELECT * FROM users_have_cards WHERE cardid = " + card[0] + " AND userid = " + session['user'])
            r = cursor2.first()
            if r is None:
                g.conn.execute("INSERT INTO users_have_cards VALUES (" + card[0] + ", " + session['user'] + ")")
            cursor2.close()
        cursor.close()
        return render_template("open_pack.html", **context)

def chooseFive(r):
    total = 0
    for row in r:
        total += row[4]
    cards = [randint(1, total), randint(1, total), randint(1, total), randint(1, total), randint(1, total)]
    cards.sort()
    total = 0
    result = []
    i = 0
    for row in r:
        total += row[4]
        while i < 5 and cards[i] <= total:
            result.append((row[0],row[1]))
            i += 1
        if i > 4:
            break
    return result


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using

            python server.py

        Show the help text using

            python server.py --help

        """

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
