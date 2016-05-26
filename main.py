# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import json, os, psycopg2, urlparse

app = Flask(__name__)
app.debug = True

##################################################################

def db_init():
    """Cette fonction crée la connexion à la base de données et renvoie,
       l'objet de connexion et un curseur."""

    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    cur = conn.cursor()    
    return conn, cur

def db_createTables(conn, cur):
  """Cette fonction initialise la base de données. Elle est invoquée par
     un chemin spécial - voir /debug/db/reset"""

  cur.execute('''\
    DROP TABLE IF EXISTS Product;
    DROP TABLE IF EXISTS Basket;
    DROP TABLE IF EXISTS Utilisateur;
    CREATE TABLE Product (
      pid SERIAL,
      name varchar,
      price float,
      description varchar
    );
    CREATE TABLE Basket (
      bid SERIAL,
      uuid varchar,
      product_ref varchar,
      product_qt int
    );
    CREATE TABLE Utilisateur (
      uid SERIAL,
      name varchar,
      pass varchar
    );
    INSERT INTO Product (name, price, description) VALUES ('Pomme', 1.20, 'Fruit rond vert, rouge, jaune...');
    INSERT INTO Product (name, price, description) VALUES ('Poire', 1.60, 'Fruit cool');
    INSERT INTO Product (name, price, description) VALUES ('Fraise', 3.80, 'Fruit rouge sucre');
    INSERT INTO Basket  (uuid, product_ref, product_qt) VALUES ('1234-1234-1234', '55lk32', 5);
    INSERT INTO Utilisateur (name, pass) VALUES ('admin','admin');
    ''')
  conn.commit()

def db_select(cur, sql, params = None):
  """Cette fonction exécute une requête SQL de type SELECT
     et renvoie le résultat avec pour chaque ligne un dictionnaire
     liant les noms de colonnes aux données."""

  if params:
    cur.execute(sql, params)
  else:
    cur.execute(sql)

  rows = cur.fetchall()
  cleanRows = []
  if rows != None:
    columns = map(lambda d: d[0], cur.description)
    for row in rows:
      cleanRow = dict()
      for (i,colName) in enumerate(columns):
        cleanRow[colName] = row[i]
      cleanRows.append(cleanRow)

  return cleanRows

##################################################################

@app.route('/debug/db/reset')
def route_dbinit():
  """Cette route sert à initialiser (ou nettoyer) la base de données."""

  conn, cur = db_init()
  db_createTables(conn, cur)
  conn.close()
  return "Done."

#-----------------------------------------------------------------

@app.route('/products')
def products_fetchall():
  """Exemple d'une requête qui exécute une requête SQL et renvoie
     le résultat."""

  conn, cur = db_init()
  result = db_select(cur, 'SELECT * FROM Product')
  conn.close()

  resp = make_response(json.dumps(result))
  resp.mimetype = 'application/json'
  return resp

#-----------------------------------------------------------------

@app.route('/products/<int:productId>')
def product_description(productId):
  conn, cur = db_init()
  result = db_select(cur, 'SELECT * FROM Product WHERE pid=%(pid)s', {
    "pid": productId
  })
  conn.close()
  
  resp = make_response(json.dumps(result))
  resp.mimetype = 'application/json'
  return resp
 
#-----------------------------------------------------------------

@app.route('/products', methods = ['POST'])
def post_product():
  conn, cur = db_init();
  req = request.get_json();
  cur.execute("INSERT INTO Product (name,price,description) VALUES (%(name)s,%(price)s,%(description)s)", {
    "name" : req['name'], 
    "description" : req['description'],
    "price" : req['price']
  })
  conn.commit()
  conn.close()

  return "OK"

#-----------------------------------------------------------------

@app.route('/baskets')
def basket_fetchall():
  conn, cur = db_init()
  result = db_select(cur, 'SELECT * FROM Basket')
  conn.close()

  resp = make_response(json.dumps(result))
  resp.mimetype = 'application/json'
  return resp

#-----------------------------------------------------------------

@app.route('/baskets/<basketUuid>', methods=['GET'])
def basket_fetchOne(basketUuid):
  conn, cur = db_init()
  baskets = db_select(cur, 'SELECT * FROM Basket WHERE bid=%(bid)s',{
    "bid" : basketUuid
  })
  conn.close()
  
  resp = make_response(json.dumps(baskets), 200)
  resp.mimetype = 'application/json'
  return resp

#-----------------------------------------------------------------

@app.route('/baskets/<basketUuid>', methods = ['POST'])
def basket_addItem(basketUuid):
  name = request.authorization.username
  passw = request.authorization.password
  
  conn, cur = db_init()
  nameauth = db_select(cur, 'SELECT name FROM Utilisateur')
  passauth = db_select(cur, 'SELECT pass FROM Utilisateur')
  conn.close()
    
  if (name == nameauth[0]['name']) and (passw == passauth[0]['pass']):
    auth = True
  else :
    auth = False
  
  if auth :
    product_ref = request.args.get('product_ref','')
    product_qt = request.args.get('product_qt', '')
    
    conn, cur = db_init()
    cur.execute('UPDATE Basket SET product_ref = %(ref)s , product_qt = %(qt)s WHERE bid = %(uuid)s', {
      'uuid' : basketUuid,
      'ref' : product_ref,
      'qt' : product_qt
    })
    conn.commit()
  
    resp = make_response(json.dumps(product_ref + ' : ' + product_qt))
    resp.mimetype = 'application/json'
  else :
    return authenticate()

  return resp
 
 #-----------------------------------------------------------------
 
def authenticate():
    """Sends a 401 response that enables basic auth"""
    return make_response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'}) 

#-----------------------------------------------------------------

if __name__ == "__main__":
  app.run()