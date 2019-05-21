import pymysql
import pymysql.cursors
from constants import RANG
from ConnectDB import DbUtil
from flask import Blueprint, render_template, redirect, request, session
routeTags = Blueprint('tags', __name__, template_folder='templates')

@routeTags.route('/list')
def list():
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM t_tag ORDER BY Tag")
				data_tags = cursor.fetchall()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return render_template('tags/list.html', tags=data_tags)
	return render_template('erreurs/403.html'), 403

@routeTags.route('/edit', methods=['GET', 'POST'])
@routeTags.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id = 0):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			if request.method == 'GET':
				if id:
					try:
						connection = DbUtil.get_connection()
						cursor = connection.cursor()
						cursor.execute("SELECT * FROM t_tag WHERE ID_Tag = %s", id)
						data_tag = cursor.fetchone()
					except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
						print("Problème avec la BD ! : %s", error)
						connection.rollback()
					finally:
						connection.close()
						cursor.close()
				else :
					data_tag = None
				return render_template('tags/edit.html', tag = data_tag)
			if request.method == 'POST':
				ID_Tag = request.form['id']
				Tag = request.form['tag']
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				if ID_Tag:
					cursor.execute("UPDATE t_tag SET Tag = %s WHERE ID_Tag = %s", (Tag, ID_Tag))
				else:
					cursor.execute("INSERT INTO t_tag(Tag) VALUES(%s)", Tag)
				connection.commit()
				return redirect('/tags/list')
	return render_template('erreurs/403.html'), 403

@routeTags.route('/delete/<int:id>')
def delete(id):
	if 'ID_Client' in session:
		if session['Rang'] >= RANG['VENDEUR']:
			try:
				connection = DbUtil.get_connection()
				cursor = connection.cursor()
				cursor.execute("DELETE FROM t_tag WHERE ID_Tag = %s", id)
				connection.commit()
			except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
				print("Problème avec la BD ! : %s", error)
				connection.rollback()
			finally:
				connection.close()
				cursor.close()
				return redirect('/tags/list')
	return render_template('erreurs/403.html'), 403
