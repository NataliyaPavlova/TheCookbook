import json
import pprint
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from helpers import cookbook, meets_conditions, find_recipe, search_recipes, str_to_list, login_required, apology

# Configure application
app = Flask(__name__)

'''
# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
'''
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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

        # Query database for username
        #rows = db.execute("SELECT * FROM users WHERE username = :username",
        #                  username=request.form.get("username"))
        rows = db.session.query(Users).filter(login == request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

        #hashing the password generate_password_hash
        hash = generate_password_hash(request.form.get("password"))

        #insert user into the db
        #result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
        #                        username = request.form.get("username"), hash=hash )
        user = Users(login=request.form.get("username"), password=hash, favorites=[], allergies=[])
        try:
            db.session.add(user)
            db.session.commit()
        except:
            return apology("the username is already used...", 403)

        #Query database for username
        #result = db.execute("SELECT * FROM users WHERE username = :username",
        #                    username=request.form.get("username"))


        #remember who is registered
        session["user_id"] = request.form.get("username")

     # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

    # Redirect user to home page
    return redirect("/")


@app.route("/filter", methods = ['GET', 'POST'])
@login_required
def filter():
    ''' Show filter forms to user'''

    #upload user's allergies from db
    result1 = db.execute("SELECT allergies FROM users WHERE id=:id", id=session["user_id"])
    if not result1:
        return apology("the operation is impossible, try again later...", 403)

    #make a list from a string
    if result1[0]['allergies']:
        user_allergies = str_to_list(result1[0]['allergies'])
    else:
        user_allergies=[]

    #send to filter.html with a list of allergies
    return render_template('/filter.html', user_allergies=user_allergies)


@app.route("/search_result", methods = ['GET', 'POST'])
@login_required
def search_result():
    ''' Find and show search results to user'''

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

@app.route("/recipe_search", methods = ['GET', 'POST'])
@login_required
def recipe_search():
    ''' Forward user from search_result page to recipe page'''

    title = request.args['title']
    recipe = find_recipe(title)

    return render_template('/recipe_search.html', recipe=recipe)


@app.route("/recipe_favor", methods = ['GET', 'POST'])
@login_required
def recipe_favor():
    ''' Forward user from index (favorites) page to recipe page'''

    title = request.args['title']
    recipe = find_recipe(title)

    return render_template('/recipe_favor.html', recipe=recipe)


@app.route("/add_recipe_search", methods = ['GET', 'POST'])
@login_required
def add_recipe_search():
    ''' Add recipe to user's favorites'''

    # via GET method get title of recepie to add
    title = request.args['title']+' '

    # from db get the list of IDs of user's favorite recepies
    result1 = db.execute("SELECT * FROM users WHERE id=:id", id=session["user_id"])
    if not result1:
        return apology("the operation is impossible, try again later...", 403)

    if result1[0]['favorites']:
        recipes = str_to_list(result1[0]['favorites'])
    else:
        recipes=[]


    # from db get id using recepie's title
    result2 = db.execute("SELECT * FROM recipes WHERE title=:title", title=title)
    if not result2:
        return apology("the operation is impossible, try again later...", 403)

    # update the list of favorites and upload it to db
    if not str(result2[0]['id']) in recipes:
        recipes.append(result2[0]['id'])

    result3 = db.execute("UPDATE users SET favorites=:favorites WHERE id=:id",
                        favorites=str(recipes), id=session["user_id"] )
    if not result3:
        return apology("the operation is impossible, try again later...", 403)

    title=title[:-1]
    recipe = find_recipe(title)
    return render_template('/recipe_search.html', recipe=recipe)


@app.route("/", methods = ['GET', 'POST'])
@login_required
def index():
    ''' Show user's favorite recipes'''

    recipes_result=[]
    #load the list of IDs of favorite recipes
    result1 = db.execute("SELECT favorites FROM users WHERE id=:id", id=session["user_id"])

    if result1[0]['favorites']:
        id_favorites = str_to_list(result1[0]['favorites'])
    else:
        return render_template('/index.html', results_number=0, recipes_result=recipes_result)

    #looking for a title for every id in the list, making the list of titles
    for id in id_favorites:
        result2 = db.execute("SELECT title FROM recipes WHERE id=:id", id=id)
        if not result2:
            return apology("the operation is impossible, try again later...", 403)
        recipes_result.append(result2[0]['title'])

    return render_template('/index.html', results_number=len(recipes_result), recipes_result=recipes_result)


@app.route("/process", methods = ['GET', 'POST'])
@login_required
def process():
    ''' Process user's input, load it to db and send it to search_result function'''

    mark_allergies=[]
    preferencies=[]
    meal=''

    # No ensure in user's input is needed: no activated cheboxes - no allergy
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
        preferencies.append('Sugar Concious')
        preferencies.append('Low/No Sugar')
        preferencies.append('Healthy')


    if request.form.get("Quick&Easy"):
        preferencies.append('Quick & Easy')
        preferencies.append('Quick and Healthy')
        preferencies.append('22-Minute Meals')
        preferencies.append('3-Ingredient Recipes')



    result1 = db.execute("UPDATE users SET preferencies=:preferencies WHERE id=:id",
                        preferencies=str(preferencies), id=session["user_id"])
    if not result1:
        return apology("the operation is impossible, try again later...", 403)

    result2 = db.execute("UPDATE users SET allergies=:allergies WHERE id=:id",
                         allergies=str(mark_allergies), id=session["user_id"])
    if not result2:
        return apology("the operation is impossible, try again later...", 403)

    result3 = db.execute("UPDATE users SET meal=:meal WHERE id=:id",
                         meal=meal, id=session["user_id"])
    if not result3:
        return apology("the operation is impossible, try again later...", 403)

    recipes_result = search_recipes(mark_allergies, preferencies, meal)

    return render_template('search_result.html', recipes_result=recipes_result, results_number=len(recipes_result))


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
