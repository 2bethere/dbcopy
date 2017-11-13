from flask import Flask
from flask import render_template, redirect, url_for, request, flash
from flask import jsonify
import psycopg2 as dbapi2
from psycopg2 import sql
import dbutil
import os

app = Flask(__name__)
app.debug = True
app.secret_key = DB_PORT = os.environ['SECRET_KEY'];

@app.route('/')
def home():
    db = dbapi2.connect (host=dbutil.DB_HOST,  database=dbutil.BASE_DB, user=dbutil.DB_USER, password=dbutil.DB_PASS)
    db.autocommit = True
    cur = db.cursor()
    cur.execute('SELECT datname FROM pg_database WHERE datistemplate = false;')
    result = cur.fetchall()
    app.logger.debug(result);
    for item in dbutil.DB_BLACKLIST:
        try:
            result.remove((item,))
        except ValueError:
            pass
    cur.close()
    db.close()
    return render_template('index.html',db_list = result)

@app.route('/check/<name>')
def check(name=None):
    db = dbapi2.connect (host=dbutil.DB_HOST,  database=dbutil.BASE_DB, user=dbutil.DB_USER, password=dbutil.DB_PASS)
    db.autocommit = True
    cur = db.cursor()
    cur.execute('SELECT datname FROM pg_database WHERE datistemplate = false AND datname = %s',(name,))    
    cur.close()
    db.close()
    if cur.rowcount > 0:
        return jsonify(dbexist=True)
    else:
        return jsonify(dbexist=False)
    
@app.route('/create/')
def create():
    name = request.args.get('name', '')
    db = dbapi2.connect (host=dbutil.DB_HOST,  database=dbutil.BASE_DB, user=dbutil.DB_USER, password=dbutil.DB_PASS)
    db.autocommit = True
    cur = db.cursor()
    #CREATE ROLE patrick WITH LOGIN PASSWORD 'Getting started';
    cur.execute(
         sql.SQL("CREATE ROLE {user} WITH LOGIN PASSWORD '123456'")
         .format(user=sql.Identifier(name+"_user"))
         )
    #Create a copy of the database
    cur.execute(
         sql.SQL("CREATE DATABASE {dest} OWNER {owner} TEMPLATE {src}")
         .format(dest=sql.Identifier(name),owner=sql.Identifier(name+"_user"), src=sql.Identifier(dbutil.BASE_DB))
         )
    #Create new user and grant access to the the database
    #GRANT ALL PRIVILEGES ON DATABASE super_awesome_application TO patrick;
    cur.execute(
         sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}")
         .format(db=sql.Identifier(name),user=sql.Identifier(name+"_user"))
         )
    #Reassign ownership
    cur.execute(
         sql.SQL("ALTER DATABASE {db} OWNER TO {user}")
         .format(db=sql.Identifier(name),user=sql.Identifier(name+"_user"))
         )
    cur.close()
    db.close()
    #Reconnect and reassign table ownerships
    db = dbapi2.connect (host=dbutil.DB_HOST,  database=name, user=dbutil.DB_USER, password=dbutil.DB_PASS)
    db.autocommit = True
    cur = db.cursor()
    cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\'')
    tables = cur.fetchall()
    for table in tables:
        cur.execute(
            sql.SQL("ALTER TABLE {table_name} OWNER TO {user}")
            .format(table_name=sql.Identifier(table[0]),user=sql.Identifier(name+"_user"))
        )
    cur.close()
    db.close()
    flash('Database '+ name +' created')
    return redirect(url_for('home'))

@app.route('/delete/<name>')
def delete(name=None):
    db = dbapi2.connect (host=dbutil.DB_HOST,  database=dbutil.BASE_DB, user=dbutil.DB_USER, password=dbutil.DB_PASS)
    db.autocommit = True
    cur = db.cursor()
    #drop database
    cur.execute(
            sql.SQL("DROP DATABASE IF EXISTS {db_name}")
            .format(db_name=sql.Identifier(name))
        )
    #drop role
    cur.execute(
            sql.SQL("DROP USER IF EXISTS {user}")
            .format(user=sql.Identifier(name+"_user"))
        )
    cur.close()
    db.close()
    flash('Database '+ name +' deleted')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(use_debugger=True, debug=app.debug)
