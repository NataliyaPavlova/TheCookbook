#import json
#import pprint
import os
from werkzeug.exceptions import default_exceptions
from flask import redirect, render_template, request, session
#from flask_session import Session

from models import Users, Recipes, db_init
from utils import app
from helpers import login_required, apology

# init and fulfill the db
# 'allergies.json' - allergy's type and common products containing the allergen
# 'full_format_recipes.json' - recipes collection from kaggle
basepath = os.path.abspath(".")
db_init(basepath + '/static/allergies.json', basepath + '/static/full_format_recipes.json')

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        result = Users.check_login(request.form.get("username"), request.form.get("password") )
        if not result:
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = result

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("missing username...", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("missing password...", 403)

        # Ensure confirmation of the password was submitted
        elif not request.form.get("confirm_password"):
            return apology("missing password confirmation...", 403)

        elif not request.form.get("password")==request.form.get("confirm_password"):
            return apology("password confirmation fails ...", 403)

        result = Users.register(request.form.get("username"), request.form.get("password"))
        if not result:
            return apology("the username is already used...", 403)

        #remember who is registered
        session["user_id"] = result

     # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

    # Redirect user to home page
    return redirect("/")


@app.route("/filter", methods = ['GET', 'POST'])
@login_required
def filter():
    ''' Show filter forms with user's allergies '''

    #upload user's allergies from db
    user_allergies = Users.get_allergens(session["user_id"])

    #send to filter.html with a list of allergies
    return render_template('/filter.html', user_allergies=user_allergies)

'''
@app.route("/search_result", methods = ['GET', 'POST'])
@login_required
def search_result():
    # Find and show search results to user

    #upload user's allergies and preferencies from db
    result1 = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
    if not result1:
        return apology("the operation is impossible, try again later...", 403)

    #make a list from a string
    if result1[0]['allergies']:
        mark_allergies = str_to_list(result1[0]['allergies'])
    else:
        mark_allergies=[]

    if result1[0]['preferencies']:
        user_preferencies = str_to_list(result1[0]['preferencies'])
    else:
        user_preferencies=[]

    if result1[0]['meal']:
        meal = result1[0]['meal']
    else:
        meal=''

    #search in cookbook
    recipes_result = search_recipes(mark_allergies, user_preferencies, meal)

    #send to html with a list recipes' titles
    return render_template('/search_result.html', recipes_result=recipes_result, results_number = len(recipes_result))
'''

@app.route("/recipe_search", methods = ['GET', 'POST'])
@login_required
def recipe_search():
    ''' Forward user from search_result page to recipe page'''

    title = request.args['title']
    recipe = Recipes.get_recipe(title)

    return render_template('/recipe_search.html', recipe=recipe)


@app.route("/recipe_favor", methods = ['GET', 'POST'])
@login_required
def recipe_favor():
    ''' Forward user from index (favorites) page to recipe page'''

    title = request.args['title']
    recipe = Recipes.get_recipe(title)

    return render_template('/recipe_favor.html', recipe=recipe)


@app.route("/add_recipe_search", methods = ['GET', 'POST'])
@login_required
def add_recipe_search():
    ''' Add recipe to user's favorites'''

    # via GET method get title of recipe to add
    title = request.args['title']+' '

    recipe = Users.add_to_favorites(session['user_id'], title)

    return render_template('/recipe_search.html', recipe=recipe)


@app.route("/", methods = ['GET', 'POST'])
@login_required
def index():
    ''' Show user's favorite recipes'''

    favorite_titles = Users.get_favorites(session['user_id'])
    return render_template('/index.html', results_number=len(favorite_titles), recipes_result=favorite_titles)


@app.route("/process", methods = ['GET', 'POST'])
@login_required
def process():
    ''' Process user's input, load it to db and send it to search_result function'''

    mark_allergies=[]
    preferencies=[]
    meal=''

    # No ensure in user's input is needed: no activated checkboxes - no allergy
    if not request.method == "POST":
        return render_template('/filter.html')

    # make user's list of allergies
    if request.form.get("Gluten/Wheat"):
        mark_allergies.append('gluten')
    if request.form.get("Dairy"):
        mark_allergies.append('dairy')
    if request.form.get("Eggs"):
        mark_allergies.append('eggs')
    if request.form.get("Nuts"):
        mark_allergies.append('nuts')
    if request.form.get("Soy"):
        mark_allergies.append('soy')
    if request.form.get("Honey"):
        mark_allergies.append('honey')
    if request.form.get("Seafood"):
        mark_allergies.append('seafood')

     # make user's meal and list of preferencies (diets and other)
    if request.form.get("meal"):
        meal = request.form.get("meal")

    if request.form.get("Vegetarian"):
        preferencies.append('Vegan')
        preferencies.append('Vegetarian')
        preferencies.append('Vegetable')
    if request.form.get("Kosher"):
        preferencies.append('Kosher')
    if request.form.get("Low Fat"):
        preferencies.append('Low Fat')
        preferencies.append('Healthy')
    if request.form.get("Low Sugar"):
        preferencies.append('Low Sugar')
        preferencies.append('Sugar Conscious')
        preferencies.append('Low/No Sugar')
        preferencies.append('Healthy')


    if request.form.get("Quick&Easy"):
        preferencies.append('Quick & Easy')
        preferencies.append('Quick and Healthy')
        preferencies.append('22-Minute Meals')
        preferencies.append('3-Ingredient Recipes')

    # update user's allergies
    Users.update_allergies(session['user_id'], mark_allergies)
    # search for the recipes
    found_recipes = Users.search_recipes(session['user_id'], preferencies, meal)

    return render_template('search_result.html', recipes_result=found_recipes, results_number=len(found_recipes))


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

