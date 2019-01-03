#import json
#import pprint
#import re
#from collections import Counter
#from flask import redirect, render_template, request, session
#from functools import wraps
from db_description import Allergies, Recipes, Recipes_Allerg
from utils import db


def get_allergens():
    ''' get allergens (dict) from db table Allergies'''

    # Retrieve data from db
    dct_allergens = {}
    lst_allergens = Allergies.query.all()
    for row in lst_allergens:
        dct_allergens[row.allergen] = row.key_words
    return dct_allergens


def put_to_rec_all(title, lst_allergens):
    ''' insert into db recipe's id and allergen's id '''

    # find recipe's id based on its title (titles are unique)
    recipe_id = db.session.query(Recipes).filter(Recipes.title==title).scalar()
    # for each allergen find its id and put (recipe.id, allergen.id) to the table
    for allergen in lst_allergens:
        allergen_id = db.session.query(Allergies).filter(Allergies.allergen==allergen).scalar()
        pair = Recipes_Allerg(recipe_id=recipe_id, allergen_id=allergen_id)
        db.session.add(pair)
    db.session.commit()


'''

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code




def meets_conditions(mark_allergies, recipe, allergies, preferencies, meal):
    ''' Returns True if a recipe meets the allergy conditions (no allergens in categories and ingredients) and user's given preferencies'''

    marker=0 #marker for preferencies
    if not 'categories' in recipe.keys():
        return False

    categories = list(map(lambda x: x.lower(), recipe["categories"]))
    preferencies = list(map(lambda x: x.lower(), preferencies))

    #check allergy criteria
    for allerg in mark_allergies:
        #check if category is allergic
        for category in categories:
            if category in allergies[allerg]:
                return False

        #check if allergen is in ingredients
        if check_ingr(recipe['ingredients'], allerg, allergies):
            return False

    #check meal criteria
    if meal=='snack':
        if not (meal in categories) and not ("hors d'oeuvre" in categories):
            return False
    else:
        if not meal in categories and not meal=='':
            return False

    #check preferencies criteria: if at least one preference fits categories, it's true
    '''if all(x in recipe["categories"] for x in preferencies):
        marker=1'''
    for category in categories:
        if category in preferencies:
            marker=1
    if not marker==1 and not preferencies==[]:
        return False


    return True



'''
