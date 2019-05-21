import pymysql
import pymysql.cursors
from ConnectDB import DbUtil
from constants import RANG
from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
routeUtilisateur = Blueprint('utilisateur', __name__, template_folder='templates')

@routeUtilisateur.route('/login', methods=['GET', 'POST'])
def login():

	if request.method == 'GET':
		if not 'Pseudo' in session:
			session['Pseudo'] = ''
		return render_template('utilisateur/login.html', username=session['Pseudo'])
	if request.method == 'POST':

		session['Pseudo'] = request.form['username']

		if not request.form['username'] or not request.form['password']:
			return render_template('utilisateur/login.html', msg="fields", username=session['Pseudo'])

		try:
			connection = DbUtil.get_connection()
			cursor = connection.cursor()

			cursor.execute("SELECT ID_Client, Pseudo, Mot_de_passe, Nom, Prenom, Date_Inscription, Rang FROM t_client WHERE Pseudo = %s", request.form['username'])
			data_client = cursor.fetchone()
		except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
			print("Problème avec la BD ! : %s", error)
			connection.rollback()
		finally:
			connection.close()
			cursor.close()

		if data_client is None:
			return render_template('utilisateur/login.html', msg="username", username=session['Pseudo'])

		#fonction qui vérifie le mot de passe
		if check_password_hash(data_client['Mot_de_passe'], request.form['password']):

			#On enregistre toutes les données dans des variables de session
			session['ID_Client'] = data_client['ID_Client']
			session['Pseudo'] = data_client['Pseudo']
			session['Nom'] = data_client['Nom']
			session['Prenom'] = data_client['Prenom']
			session['Date_Inscription'] = data_client['Date_Inscription']
			session['Titre'] = get_titre(data_client['Rang'])
			session['Rang'] = data_client['Rang']
			return redirect('/utilisateur/utilisateur')
		else:
			return render_template('utilisateur/login.html', msg="password", username=session['Pseudo'])

@routeUtilisateur.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		if not 'Pseudo' in session:
			session['Pseudo'] = ''
		if not 'Nom' in session:
			session['Nom'] = ''
		if not 'Prenom' in session:
			session['Prenom'] = ''
		return render_template('utilisateur/register.html', username=session['Pseudo'], nom=session['Nom'], prenom=session['Prenom'])
	if request.method == 'POST':
		session['Pseudo'] = request.form['username']
		session['Nom'] = request.form['nom']
		session['Prenom'] = request.form['prenom']

		if not request.form['username'] or not request.form['password'] or not request.form['confirm_password'] or not request.form['nom'] or not request.form['prenom']:
			return render_template('utilisateur/register.html', msg="fields", username=session['Pseudo'], nom=session['Nom'], prenom=session['Prenom'])
		
		if request.form['password'] != request.form['confirm_password']:
			return render_template('utilisateur/register.html', msg="password", username=session['Pseudo'], nom=session['Nom'], prenom=session['Prenom'])

		try:
			connection = DbUtil.get_connection()
			cursor = connection.cursor()

			cursor.execute("SELECT ID_Client FROM t_client WHERE Pseudo = %s", request.form['username'])
			data_exist = cursor.fetchone()

			if data_exist is not None:
				connection.close()
				cursor.close()
				return render_template('utilisateur/register.html', msg="username", username=session['Pseudo'], nom=session['Nom'], prenom=session['Prenom'])

			cursor.execute("INSERT INTO t_client(Pseudo, Mot_de_passe, Nom, Prenom) VALUES(%s, %s, %s, %s)", (request.form['username'], generate_password_hash(request.form['password']), request.form['nom'], request.form['prenom']))
			connection.commit()

			cursor.execute("SELECT ID_Client, Pseudo, Mot_de_passe, Nom, Prenom, Date_Inscription, Rang FROM t_client WHERE Pseudo = %s", request.form['username'])
			data_client = cursor.fetchone()
			session['ID_Client'] = data_client['ID_Client']
			session['Pseudo'] = data_client['Pseudo']
			session['Nom'] = data_client['Nom']
			session['Prenom'] = data_client['Prenom']
			session['Date_Inscription'] = data_client['Date_Inscription']
			session['Titre'] = get_titre(data_client['Rang'])
			session['Rang'] = data_client['Rang']
		except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
			print("Problème avec la BD ! : %s", error)
			connection.rollback()
		finally:
			connection.close()
			cursor.close()

			return redirect('/utilisateur/utilisateur')

@routeUtilisateur.route('/logout')
def logout():
	# on supprime simplement les variables de session
	session.pop('ID_Client', None)
	session.pop('Pseudo', None)
	session.pop('Nom', None)
	session.pop('Prenom', None)
	session.pop('Date_Inscription', None)
	session.pop('Titre', None)
	session.pop('Rang', None)
	return redirect('/')

# Affiche le profile d'un utilisateur. Si l'ID n'est pas défini alors affiche le compte de l'utilisateur connecté
@routeUtilisateur.route('/utilisateur')
@routeUtilisateur.route('/utilisateur/<int:id_client>')
def utilisateur(id_client = 0):
	if 'ID_Client' in session:
		try:
			connection = DbUtil.get_connection()
			cursor = connection.cursor()

			if id_client == 0:
				id_client = session['ID_Client']
			cursor.execute("SELECT ID_Client, Pseudo, Nom, Prenom, Date_Inscription, Rang FROM t_client WHERE ID_Client = %s", id_client)
			data_client = cursor.fetchone()
		except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
			print("Problème avec la BD ! : %s", error)
			connection.rollback()
		finally:
			connection.close()
			cursor.close()
		
		return render_template('utilisateur/utilisateur.html', client=data_client, titre=get_titre(data_client['Rang']), rang=RANG)
	else:
		return redirect('/utilisateur/login')

# page pour changer son mot de passe
@routeUtilisateur.route('/mot_de_passe', methods=['GET', 'POST'])
def mot_de_passe():
	if 'ID_Client' in session:
		if request.method == 'GET':
			return render_template('utilisateur/mot_de_passe.html')
		if request.method == 'POST':
			if not request.form['old_password'] or not request.form['new_password'] or not request.form['confirm_password']:
				return render_template('utilisateur/mot_de_passe.html', msg="fields")
			if request.form['new_password'] != request.form['confirm_password']:
				return render_template('utilisateur/mot_de_passe.html', msg="confirm_password")

			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				cursor.execute("SELECT Mot_de_passe FROM t_client WHERE ID_Client = %s", session['ID_Client'])
				data_client = cursor.fetchone()
				if not check_password_hash(data_client['Mot_de_passe'], request.form['old_password']):
					connection.close()
					cursor.close()
					return render_template('utilisateur/mot_de_passe.html', msg="old_password")
				
				cursor.execute("UPDATE t_client SET Mot_de_passe = %s WHERE ID_Client = %s", (generate_password_hash(request.form['new_password']), session['ID_Client']))
				connection.commit()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
			
			return render_template('utilisateur/mot_de_passe.html', msg="success")
	else:
		return redirect('/utilisateur/login')

# Petite fonction qui renvoie un texte correspondant au rang de la personne
def get_titre(niveau = 0):
	if niveau == RANG['VISITEUR']:
		return "Visiteur"
	if niveau == RANG['UTILISATEUR']:
		return "Client"
	if niveau == RANG['VENDEUR']:
		return "Vendeur"
	if niveau == RANG['ADMINISTRATEUR']:
		return "Super Admin"
	else:
		return "Hacker"
