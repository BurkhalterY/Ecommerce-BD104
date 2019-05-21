import pymysql
import pymysql.cursors
from ConnectDB import DbUtil
from constants import RANG
from flask import Blueprint, render_template, session
routeAdmin = Blueprint('admin', __name__, template_folder='templates')

@routeAdmin.route('/')
@routeAdmin.route('/admin')
def admin():
	if 'ID_Client' in session:
		# Affiche la page seulement si l'utilisateur est au moins de rang veudeur
		if session['Rang'] >= RANG['VENDEUR']:
			return render_template('admin/admin.html')
	# Sinon : erreur 403
	return render_template('erreurs/403.html'), 403