import pymysql
import pymysql.cursors
import os
import re
from ConnectDB import DbUtil
from constants import RANG
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.utils import secure_filename
routeProduits = Blueprint('produits', __name__, template_folder='templates')

# Page qui affiche la liste de tous les produits d'une catégorie et de ses catégories enfantes
@routeProduits.route('/list')
@routeProduits.route('/list/<int:id_categorie>')
def produits(id_categorie = 0):
	try:
		connection = DbUtil.get_connection()
		cursor = connection.cursor()

		cursor.execute("SELECT Nom_Categorie, FK_Categorie_Parent FROM t_categorie WHERE ID_Categorie = %s", id_categorie)
		data_main_categorie = cursor.fetchone()

		if id_categorie == 0:
			cursor.execute("SELECT ID_Categorie, Nom_Categorie FROM t_categorie WHERE FK_Categorie_Parent IS NULL")
		else:
			cursor.execute("SELECT ID_Categorie, Nom_Categorie FROM t_categorie WHERE FK_Categorie_Parent = %s ORDER BY Nom_Categorie", id_categorie)
		data_categories = cursor.fetchall()

		search = "%" + request.args.get('search', default="") + "%"

		if id_categorie == 0:
			# Si la catégorie = 0, on peut prendre tous les produits
			cursor.execute("SELECT ID_Produit, Nom_produit, Prix, Description, (SELECT Chemin FROM t_image WHERE FK_Produit = ID_Produit ORDER BY Position LIMIT 1) AS Chemin FROM t_produit WHERE Nom_Produit LIKE %s AND Archive = 0 ORDER BY Nom_Produit", search)
		else:
			# Sinon on utilise la fonction sous_categories() qui renvoie les IDs de tous les enfant d'une catégorie. On utilise le resultat dans la requête avec IN
			liste_categories = sous_categories(id_categorie)
			cursor.execute("SELECT ID_Produit, Nom_produit, Prix, Description, (SELECT Chemin FROM t_image WHERE FK_Produit = ID_Produit ORDER BY Position LIMIT 1) AS Chemin FROM t_produit WHERE FK_Categorie IN ("+liste_categories+") AND Nom_Produit LIKE %s AND Archive = 0 ORDER BY Nom_Produit", search)
		data_produits = cursor.fetchall()

	except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
		print("Problème avec la BD ! : %s", error)
		connection.rollback()
	finally:
		connection.close()
		cursor.close()
		
	return render_template('produits/produits.html', categories=data_categories, main_categorie=data_main_categorie, produits=data_produits, search=request.args.get('search', default=""))

# Page qui affiche un produit en détail
@routeProduits.route('/view/<int:id_produit>')
def produit(id_produit):
	try:
		connection = DbUtil.get_connection()
		cursor = connection.cursor()

		cursor.execute("SELECT ID_Produit, Nom_Produit, Prix, FK_Categorie, Description FROM t_produit WHERE ID_Produit = %s", id_produit)
		data_produit = cursor.fetchone()

		# Récupération de toutes les images
		cursor.execute("SELECT Chemin FROM t_image WHERE FK_Produit = %s ORDER BY Position", id_produit)
		data_images = cursor.fetchall()

		# Récupération de tous les noms des caractéristiques et de leur valeur
		cursor.execute("SELECT ID_Valeur_Caracteristique, Nom_Cara, Valeur FROM t_avoir_caracteristique INNER JOIN t_produit ON ID_Produit = FK_Produit INNER JOIN t_valeur_caracteristique ON ID_Valeur_Caracteristique = FK_Valeur_Caracteristique INNER JOIN t_caracteristique ON ID_Caracteristique = FK_Caracteristique WHERE ID_Produit = %s ORDER BY Nom_Cara", id_produit)
		data_caracteristiques = cursor.fetchall()

		# Liste des tags attribués
		cursor.execute("SELECT Tag FROM t_produit_avoir_tag INNER JOIN t_produit ON ID_Produit = FK_Produit INNER JOIN t_tag ON ID_Tag = FK_Tag WHERE ID_Produit = %s ORDER BY Tag", id_produit)
		data_tags = cursor.fetchall()

		# Liste des caractéristiques qui découlent d'une autre. Utiliser la table t_imposer_caracteristique directement car l'édition n'est pas implémenté dans la partie web. Mais vous pouvez voir ces effets dans le produit ID = 3
		for data_caracteristique in data_caracteristiques:
			cursor.execute("SELECT Nom_Cara, T2.Valeur FROM t_imposer_caracteristique INNER JOIN t_valeur_caracteristique AS T1 ON T1.ID_Valeur_Caracteristique = FK_Caracteristique_imposante INNER JOIN t_valeur_caracteristique AS T2 ON T2.ID_Valeur_Caracteristique = FK_Caracteristique_imposee INNER JOIN t_caracteristique ON ID_Caracteristique = T2.FK_Caracteristique WHERE T1.ID_Valeur_Caracteristique = %s ORDER BY Nom_Cara", data_caracteristique['ID_Valeur_Caracteristique'])
			data_caracteristique['Caracteristiques_sup'] = cursor.fetchall()

		# Affiche tous les commentaires postés par les utilisateurs
		cursor.execute("SELECT Texte_Commentaire, Pseudo, Date_Post FROM t_commentaire INNER JOIN t_client ON ID_Client = FK_Client WHERE FK_Produit = %s ORDER BY Date_Post DESC", id_produit)
		data_commentaires = cursor.fetchall()

		chemin = []	# Chemin est un tableau qui contient toutes les catégories parentes dans l'ordre. Il est utilisé comme fil d'Ariane
		id_categorie = data_produit['FK_Categorie']
		while id_categorie is not None:
			cursor.execute("SELECT ID_Categorie, Nom_Categorie, FK_Categorie_Parent FROM t_categorie WHERE ID_Categorie = %s ORDER BY Nom_Categorie", id_categorie)
			data_categorie = cursor.fetchone()
			chemin.insert(0, data_categorie)
			id_categorie = data_categorie['FK_Categorie_Parent']

	except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
		print("Problème avec la BD ! : %s", error)
		connection.rollback()
	finally:
		connection.close()
		cursor.close()
	
	return render_template('produits/produit.html', produit=data_produit, images=data_images, caracteristiques=data_caracteristiques, tags=data_tags, commentaires=data_commentaires, chemin=chemin, rang=RANG)

# Page réservé aux Vendeurs et Admins, sert à ajouter et modifier un produit (une seule fonction pour les deux)
@routeProduits.route('/edit', methods=['GET', 'POST'])
@routeProduits.route('/edit/<int:id_produit>', methods=['GET', 'POST'])
def produit_edit(id_produit = 0):
	if 'ID_Client' in session: # Vérification si l'utilisateur est loggé...
		if session['Rang'] >= RANG['VENDEUR']: # ...et qu'il est au minimum de rang Vendeur
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()

				if request.method == 'POST': # Si l'utilsateur envoie le formulaire
					
					catProduit = request.form['cat_produit']
					if catProduit == "0":
						catProduit = None

					if id_produit == 0: # Si l'ID = 0, on crée un nouveau produit
						cursor.execute("INSERT INTO t_produit(Nom_Produit, Prix, FK_Categorie, Description) VALUES(%s, %s, %s, %s)", (request.form['nom_produit'], request.form['prix_produit'], catProduit, request.form['description']))
						connection.commit()
						return redirect('/produits/edit/'+str(cursor.lastrowid))
					else: #Sinon, on update le produit correspondant
						cursor.execute("UPDATE t_produit SET Nom_Produit = %s, Prix = %s, FK_Categorie = %s, Description = %s WHERE ID_Produit = %s", (request.form['nom_produit'], request.form['prix_produit'], catProduit, request.form['description'], id_produit))
						connection.commit()
					
					req = request.form

					# Je parcours toutes les valeur envoyées en POST
					for key, value in req.items():
						# Si c'est une caractéristique je fais un insert ou update
						if key.startswith("caracteristique"):
							id_avoir_caracteristique = key.split("caracteristique")[1]
							if id_avoir_caracteristique == "0":
								if value != "0":
									cursor.execute("INSERT INTO t_avoir_caracteristique(FK_Produit, FK_Valeur_Caracteristique) VALUES(%s, %s)", (id_produit, value))
									connection.commit()
							else:
								cursor.execute("UPDATE t_avoir_caracteristique SET FK_Valeur_Caracteristique = %s WHERE ID_Avoir_Caracteristique = %s", (value, id_avoir_caracteristique))
								connection.commit()
						# Si c'est un delete, je delete la caractéristique consérnée. Un delete est envoyé lorsque l'on clic sur la croix à droite d'une caractéristique
						if key.startswith("delete"):
							id_avoir_caracteristique = key.split("delete")[1]
							cursor.execute("DELETE FROM t_avoir_caracteristique WHERE ID_Avoir_Caracteristique = %s", id_avoir_caracteristique)
							connection.commit()

					images = request.files.getlist("images[]")
					for image in images:
						split_filename = os.path.splitext(image.filename)
						# Formats d'images autorisés
						if image and '.' in image.filename and split_filename[1] in ['.jpe', '.jpg', '.jpeg', '.gif', '.png', '.bmp', '.ico', '.svg', '.svgz', '.tif', '.tiff', '.ai', '.drw', '.pct', '.psp', '.xcf', '.psd', '.raw', '.jfif']:
							filename = secure_filename(image.filename)
							compteur = 0
							new_filename = filename
							while os.path.exists("static/uploads/" + new_filename): #Boucle qui se charge de ne pas remplacer une image
								compteur += 1
								new_filename = split_filename[0] + '(' + str(compteur) + ')' + split_filename[1]
							image.save("static/uploads/" + new_filename)
							cursor.execute("INSERT INTO t_image(Chemin, FK_Produit) VALUES(%s, %s)", (new_filename, id_produit))
							connection.commit()

					# Supprime tous les tags du produit ...
					cursor.execute("DELETE FROM t_produit_avoir_tag WHERE FK_Produit = %s", id_produit)
					connection.commit()
					list_tags = list(map(int, re.findall('\\d+', str(request.form.getlist('tagsHidden')))))
					for tag in list_tags:
						print(tag)
						#... puis les réinsère 1 à 1
						cursor.execute("INSERT INTO t_produit_avoir_tag(FK_Produit, FK_Tag) VALUES(%s, %s)", (id_produit, tag))
						connection.commit()


				# La suite est executé que l'utilisateur soit en POST ou en GET

				cursor.execute("SELECT ID_Produit, Nom_Produit, Prix, FK_Categorie, Description FROM t_produit WHERE ID_Produit = %s", id_produit)
				data_produit = cursor.fetchone()

				cursor.execute("SELECT ID_Caracteristique, ID_Valeur_Caracteristique, FK_Caracteristique, ID_Avoir_Caracteristique FROM t_avoir_caracteristique INNER JOIN t_produit ON ID_Produit = FK_Produit INNER JOIN t_valeur_caracteristique ON ID_Valeur_Caracteristique = FK_Valeur_Caracteristique INNER JOIN t_caracteristique ON ID_Caracteristique = FK_Caracteristique WHERE ID_Produit = %s ORDER BY Nom_Cara", id_produit)
				data_caracteristiques = cursor.fetchall()

				cursor.execute("SELECT Chemin FROM t_image WHERE FK_Produit = %s ORDER BY Position", id_produit)
				data_images = cursor.fetchall()

				cursor.execute("SELECT * FROM t_valeur_caracteristique INNER JOIN t_caracteristique ON FK_Caracteristique = ID_Caracteristique ORDER BY Nom_Cara, Valeur")
				data_all_caracteristiques = cursor.fetchall()

				cursor.execute("SELECT * FROM t_tag")
				data_tags = cursor.fetchall()

				cursor.execute("SELECT FK_Tag FROM t_produit_avoir_tag WHERE FK_Produit = %s", id_produit)
				data_tags_selected = cursor.fetchall()

			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				
			return render_template('produits/produit_edit.html', produit=data_produit, caracteristiques=data_caracteristiques, images=data_images, categories_dropdown=dropdown_categorie(), all_caracteristiques=data_all_caracteristiques, id_produit=id_produit, tags=data_tags, tags_selected=data_tags_selected)
	return render_template('erreurs/403.html'), 403

@routeProduits.route('/delete/<int:id_produit>')
def produit_delete(id_produit = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				# les produits ne sont pas vraiment supprimés car ils peuvent être liés à pleins d'autres tables, ils sont "archivés"
				cursor.execute("UPDATE t_produit SET Archive=1 WHERE ID_Produit = %s", id_produit)
				connection.commit()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return redirect('/produits/list')
	return render_template('erreurs/403.html'), 403

# fonction récursive qui affiche les ID de tous les enfants d'une catégorie
def sous_categories(id_categorie):
	string_categories = ''

	try:
		connection = DbUtil.get_connection()
		cursor = connection.cursor()

		if id_categorie == 0:
			cursor.execute("SELECT ID_Categorie FROM t_categorie WHERE FK_Categorie_Parent IS NULL ORDER BY Nom_Categorie")
		else:
			cursor.execute("SELECT ID_Categorie FROM t_categorie WHERE FK_Categorie_Parent = %s ORDER BY Nom_Categorie", id_categorie)
		data_categories = cursor.fetchall()

		if string_categories:
			string_categories = string_categories + ','
		string_categories = string_categories + str(id_categorie)

		for data_categorie in data_categories:
			string_categories = string_categories + ',' + sous_categories(data_categorie['ID_Categorie'])
	except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
		print("Problème avec la BD ! : %s", error)
		connection.rollback()
	finally:
		connection.close()
		cursor.close()

	return string_categories

# fonction récursive pour afficher une liste déroulante hiérarchique
def dropdown_categorie(id_categorie = 0, ite = 0):
	try:
		connection = DbUtil.get_connection()
		cursor = connection.cursor()

		# Si premier passage dans la fonction
		if id_categorie == 0:
			cursor.execute("SELECT ID_Categorie, Nom_Categorie FROM t_categorie WHERE FK_Categorie_Parent IS NULL ORDER BY Nom_Categorie")
		else:
			cursor.execute("SELECT ID_Categorie, Nom_Categorie FROM t_categorie WHERE FK_Categorie_Parent = %s ORDER BY Nom_Categorie", id_categorie)
		data_categories = cursor.fetchall()

		for data_categorie in data_categories:
			# Ajout de "-" en fonction de la profondeurs de la catégorie
			data_categorie['Nom_Categorie'] = espace(ite, '-')+" "+data_categorie['Nom_Categorie']
			# À l'ajout de chaque catégorie, on relance la fonction pour ajouter ses enfants
			data_categorie['Enfants'] = dropdown_categorie(data_categorie['ID_Categorie'], ite+1)

	except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
		print("Problème avec la BD ! : %s", error)
		connection.rollback()
	finally:
		connection.close()
		cursor.close()
	return data_categories

# fonction qui répète un caractère x fois
def espace(nb, caractere):
	chaine = ""
	for x in range(nb):
		chaine = chaine + caractere
	return chaine