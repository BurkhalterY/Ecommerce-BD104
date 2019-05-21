import pymysql
import pymysql.cursors
from ConnectDB import DbUtil
from constants import RANG
from flask import Blueprint, render_template, redirect, request, session
routeCommentaires = Blueprint('commentaires', __name__, template_folder='templates')

#Certainement le fichier Python le plus simple de mon projet ^‿^
@routeCommentaires.route('/commentaire', methods=['POST'])
def commentaire():
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['UTILISATEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()

				cursor.execute("INSERT INTO t_commentaire(FK_Client, FK_Produit, Texte_Commentaire) VALUES(%s, %s, %s)", (session['ID_Client'], request.form['id'], request.form['commentaire']))
				connection.commit()

			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
			return redirect('/produits/view/'+str(request.form['id']))
	return render_template('erreurs/403.html'), 403