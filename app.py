from ConnectDB import DbUtil
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect
from GestionHome import routeHome
from GestionProduits import routeProduits
from GestionUtilisateur import routeUtilisateur
from GestionCategories import routeCategories
from GestionCaracteristiques import routeCaracteristiques
from GestionCommentaires import routeCommentaires
from GestionAdmin import routeAdmin
from GestionTags import routeTags

app = Flask(__name__)
app.secret_key = 'a'
app.url_map.strict_slashes = False
app.register_blueprint(routeHome, url_prefix='/')
app.register_blueprint(routeProduits, url_prefix='/produits')
app.register_blueprint(routeUtilisateur, url_prefix='/utilisateur')
app.register_blueprint(routeCategories, url_prefix='/categories')
app.register_blueprint(routeCaracteristiques, url_prefix='/caracteristiques')
app.register_blueprint(routeCommentaires, url_prefix='/commentaires')
app.register_blueprint(routeAdmin, url_prefix='/admin')
app.register_blueprint(routeTags, url_prefix='/tags')

# Page à afficher en cas d'erreur 404
@app.errorhandler(404)
def page_not_found(e):
	return render_template('erreurs/404.html'), 404

if __name__ == '__main__':
	app.secret_key = b'_5#_GRAND_PAS_ARAGORN_F4Q8z\n\xec]'
	app.debug = True
	app.run(host='127.0.0.1', port=5000)