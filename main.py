# -*- coding: utf-8 -*-
from flask import Flask, request, make_response
import json, os, psycopg2, urlparse

app = Flask(__name__)

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
    CREATE TABLE Product (
      pid SERIAL,
      name varchar,
      price float,
      description varchar
    );
    INSERT INTO Product (name, price, description) VALUES ('Pomme', 1.20, "Fruit rond vert, rouge, jaune...");
    INSERT INTO Product (name, price, description) VALUES ('Poire', 1.60, "Fruit cool");
    INSERT INTO Product (name, price, description) VALUES ('Fraise', 3.80, "Fruit rouge sucre");
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

#@app.route('/products', methods = [POST])
#def post_product():
  

#-----------------------------------------------------------------

if __name__ == "__main__":
  app.run()