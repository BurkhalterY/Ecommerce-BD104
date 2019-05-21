import pymysql
import pymysql.cursors
from ConnectDB import DbUtil
from constants import RANG
from flask import Blueprint, render_template, redirect, request, session
routeCaracteristiques = Blueprint('caracteristiques', __name__, template_folder='templates')

# Liste toutes les caractéristiques ainsi que les valeurs qu'elles peuvent prendre
@routeCaracteristiques.route('/list')
def caracteristiques():
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				cursor.execute("SELECT ID_Caracteristique, Nom_Cara FROM t_caracteristique ORDER BY Nom_Cara")
				data_caracteristiques = cursor.fetchall()
				for data_caracteristique in data_caracteristiques:
					cursor.execute("SELECT Valeur FROM t_valeur_caracteristique WHERE FK_Caracteristique = %s ORDER BY Valeur", data_caracteristique['ID_Caracteristique'])
					data_caracteristique['Valeurs'] = cursor.fetchall()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return render_template('caracteristiques/caracteristiques.html', caracteristiques=data_caracteristiques)
	return render_template('erreurs/403.html'), 403

# Modification d'une caractéristique ainsi que de ses valeurs
@routeCaracteristiques.route('/edit/<int:id_caracteristique>', methods=['GET', 'POST'])
def caracteristique(id_caracteristique = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()

				if request.method == 'POST':
					if id_caracteristique == 0: #Si nouvelle cara alors insert
						cursor.execute("INSERT INTO t_caracteristique(Nom_Cara) VALUES(%s)", (request.form['nom_cara']))
						connection.commit()
						iserted = True
						id_caracteristique = cursor.lastrowid
					else: #Si cara existante alors update
						cursor.execute("UPDATE t_caracteristique SET Nom_Cara = %s WHERE ID_Caracteristique = %s", (request.form['nom_cara'], id_caracteristique))
						connection.commit()
						iserted = False

					req = request.form

					# Boucle for sur tous les paramètre POST
					for key, value in req.items():
						if key.startswith("valeur"): # Si la paramètre commence par "valeur"
							id_valeur = key.split("valeur")[1] # On récupère le numéro qui suit valeur
							if value:
								if id_valeur == "0": # 0 si c'est une nouvelle valeur
									cursor.execute("INSERT INTO t_valeur_caracteristique(Valeur, FK_Caracteristique) VALUES(%s, %s)", (value, id_caracteristique))
									connection.commit()
								else: # Sinon, on update dans la db
									cursor.execute("UPDATE t_valeur_caracteristique SET Valeur = %s, FK_Caracteristique = %s WHERE ID_Valeur_Caracteristique = %s", (value, id_caracteristique, id_valeur))
									connection.commit()
						if key.startswith("delete"): # Même chose si ça commence par "delete"
							id_valeur = key.split("delete")[1] # On récupère l'id puis on l'efface
							cursor.execute("DELETE FROM t_valeur_caracteristique WHERE ID_Valeur_Caracteristique = %s", id_valeur)
							connection.commit()

					if iserted:
						connection.close()
						cursor.close()
						return redirect('/caracteristiques/edit/'+str(id_caracteristique))

				cursor.execute("SELECT Nom_Cara FROM t_caracteristique WHERE ID_Caracteristique = %s", id_caracteristique)
				data_caracteristiques = cursor.fetchone()

				cursor.execute("SELECT ID_Valeur_Caracteristique, Valeur FROM t_valeur_caracteristique WHERE FK_Caracteristique = %s ORDER BY Valeur", id_caracteristique)
				data_valeurs = cursor.fetchall()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return render_template('caracteristiques/caracteristique.html', caracteristique=data_caracteristiques, valeurs=data_valeurs)
	return render_template('403.html'), 403