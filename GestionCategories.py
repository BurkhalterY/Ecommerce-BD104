import pymysql
import pymysql.cursors
from ConnectDB import DbUtil
from constants import RANG
from GestionProduits import sous_categories
from flask import Blueprint, render_template, request, redirect, session
routeCategories = Blueprint('categories', __name__, template_folder='templates')

@routeCategories.route('/list', methods=['GET', 'POST'])
@routeCategories.route('/list/<int:id_categorie>', methods=['GET', 'POST'])
def categories(id_categorie = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			if request.method == 'GET':
				try:
					connection = DbUtil.get_connection()
					cursor = connection.cursor()

					# Si l'id = 0, on est à la racine
					if id_categorie == 0:
						data_categorie = { "ID_Categorie": 0, "Nom_Categorie": "Racine", "FK_Categorie_Parent": 0 }
						cursor.execute("SELECT * FROM t_categorie WHERE FK_Categorie_Parent IS NULL ORDER BY Nom_Categorie")
						data_categories = cursor.fetchall()
					else:
						cursor.execute("SELECT * FROM t_categorie WHERE ID_Categorie = %s", id_categorie)
						data_categorie = cursor.fetchone()
						cursor.execute("SELECT * FROM t_categorie WHERE FK_Categorie_Parent = %s ORDER BY Nom_Categorie", id_categorie)
						data_categories = cursor.fetchall()

				except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
					print("Problème avec la BD ! : %s", error)
					connection.rollback()
				finally:
					connection.close()
					cursor.close()
					return render_template('categories/categories.html', main_categorie=data_categorie, categories=data_categories)
			if request.method == 'POST':
				try:
					connection = DbUtil.get_connection()
					cursor = connection.cursor()

					#UPDATE avec le nom et la parent cat
					cursor.execute("UPDATE t_categorie SET Nom_Categorie = %s, FK_Categorie_Parent = %s WHERE ID_Categorie = %s", (request.form['nom_categorie'], request.form['parent'], request.form['id_categorie']))
					connection.commit()
				except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
					print("Problème avec la BD ! : %s", error)
					connection.rollback()
				finally:
					connection.close()
					cursor.close()
					return "OK"
	return render_template('erreurs/403.html'), 403

@routeCategories.route('/detail/<int:id_categorie>', methods=['GET', 'POST'])
def categorie(id_categorie = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			if request.method == 'GET':
				try:
					connection = DbUtil.get_connection()
					cursor = connection.cursor()

					if id_categorie == 0:
						data_categorie = { "ID_Categorie": 0, "Nom_Categorie": "", "FK_Categorie_Parent": int(request.args.get('parent')) }
						liste_categories = "0"
					else:
						cursor.execute("SELECT * FROM t_categorie WHERE ID_Categorie = %s", id_categorie)
						data_categorie = cursor.fetchone()
						liste_categories = sous_categories(id_categorie)
					
					cursor.execute("SELECT * FROM t_categorie WHERE ID_Categorie NOT IN (%s) ORDER BY Nom_Categorie" % liste_categories)
					data_categories_dropdown = cursor.fetchall()
				except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
					print("Problème avec la BD ! : %s", error)
					connection.rollback()
				finally:
					connection.close()
					cursor.close()
					return render_template('categories/categorie.html', main_categorie=data_categorie, categories_dropdown=data_categories_dropdown)
			if request.method == 'POST':
				try:
					connection = DbUtil.get_connection()
					cursor = connection.cursor()
					if id_categorie == 0:
						if request.form['parent_cat'] == "0":
							cursor.execute("INSERT INTO t_categorie(Nom_Categorie) VALUES(%s)", request.form['nom_cat'])
						else:
							cursor.execute("INSERT INTO t_categorie(Nom_Categorie, FK_Categorie_Parent) VALUES(%s, %s)", (request.form['nom_cat'], request.form['parent_cat']))
					else:
						if request.form['parent_cat'] == "0":
							cursor.execute("UPDATE t_categorie SET Nom_Categorie = %s, FK_Categorie_Parent = NULL WHERE ID_Categorie = %s", (request.form['nom_cat'], id_categorie))
						else:
							cursor.execute("UPDATE t_categorie SET Nom_Categorie = %s, FK_Categorie_Parent = %s WHERE ID_Categorie = %s", (request.form['nom_cat'], request.form['parent_cat'], id_categorie))
					connection.commit()
				except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
					print("Problème avec la BD ! : %s", error)
					connection.rollback()
				finally:
					connection.close()
					cursor.close()
					return redirect('/categories/list/'+request.form['parent_cat'])
	return render_template('erreurs/403.html'), 403

@routeCategories.route('/delete/<int:id_categorie>')
def categorie_delete(id_categorie = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				cursor.execute("DELETE FROM t_categorie WHERE ID_Categorie = %s", id_categorie)
				connection.commit()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return redirect(request.referrer)
	return render_template('erreurs/403.html'), 403
