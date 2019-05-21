from flask import Blueprint, redirect
routeHome = Blueprint('home', __name__, template_folder='templates')

# Page d'accueil
@routeHome.route('/')
def index():
	return redirect('/produits/list')