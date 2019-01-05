#!/usr/bin/python3
import json
import flask
import sqlalchemy
from sqlalchemy_utils import ScalarListType
from werkzeug.security import check_password_hash, generate_password_hash

from utils import db

# Describe database structure

class Users(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), unique=True)
    favorites = db.Column(ScalarListType(db.Integer))  #list of recipes' id
    allergies = db.Column(ScalarListType(db.Integer)) #list of user's allergies
    password = db.Column(db.String(255), nullable=False)


    def register(self, login, password):
        ''' add a new user to users db '''

        hash = generate_password_hash(password)
        user = Users(login=login,
                     password=hash,
                     favorites=[],
                     allergies=[])
        try:
            db.session.add(user)
            db.session.commit()
        except sqlalchemy.exc:
            db.session.rollback()
            return False
        return db.session.query(Users.id).filter(Users.login==login).scalar()


    def check_login(self, login, password):
        ''' check if the user is in db and if the password is correct'''

        row = db.session.query(Users).filter(Users.login==login).one_or_none()

        # Ensure username exists and password is correct
        if not row or not check_password_hash(row.password, password):
            return False
        return row.id


    def search_recipes(self, user_id, preferences, meals):
        ''' search recipes based on conditions and return a list of recipes' ids'''

        results = db.session.query(Recipes.id).\
            filter(Recipes.categories.contains([preferences.extend(meals)])).\
            filter(sqlalchemy.not_(Recipes.allergens.contains([self.get_allergens(user_id)]))).all()

        return results

    def update_allergies(self, user_id, allergies):
        ''' update user's allergies after filling him a filter form '''
        allergens = [db.session.query(Allergies.id).filter(Allergies.allergen==allergy).scalar() for allergy in allergies]
        db.session.query(Users).get(user_id).update({'allergens': allergens})
        db.session.commit()

    def get_favorites(self, user_id):
        ''' get the user's favorites and return the list of id '''
        favorite_titles = db.session.query(Recipes.title).\
            filter(Recipes.id.in_(db.session.query(Users.favorites).getr(user_id).scalar())).\
            all()
        return favorite_titles

    def add_to_favorites(self, user_id, title):
        ''' add a recipe' id to user's favorites and returns added recipe as a dict'''
        favorites = self.get_favorites(user_id)
        recipe = Recipes.get_recipe(title)
        favorites.append(recipe['id'])
        db.session.query(Users).get(user_id).update({'favorites': favorites})
        db.session.commit()
        return recipe

    def get_allergens(self, user_id):
        ''' get the user's allergens and return the list of id '''
        allergens = db.session.query(Users.allergies).get(user_id).scalar()
        return allergens

    def vote(self, recipe_id):
        ''' adds +1 to recipe's rating '''
        db.session.query(Recipes).get(recipe_id).update({"rating": (Recipes.rating + 1)})
        db.session.commit()


class Recipes(db.Model):

    __tablename__='recipes'

    id = db.Column(db.Integer, primary_key=True)
    directions = db.Column(db.String(255))
    title = db.Column(db.String(255))
    ingredients = db.Column(ScalarListType())
    categories = db.Column(ScalarListType())
    allergens = db.Column(ScalarListType(db.Integer))
    rating = db.Column(db.Integer)

    def check_allergies(self, *components):
        ''' returns the list of allergens based on ingredients and categories'''
        allergens = []

        #get allergens from db table 'Allergies'
        dct_allergens = self.get_allergens()

        # check if there are allergens and make a list
        for component in components:
            allergens.extend(check_recipe(component, dct_allergens))
        return allergens

    def get_allergens(self):
        ''' get allergens (dict) from db table Allergies'''

        # Retrieve data from db
        dct_allergens = {}
        lst_allergens = db.session.query(Allergies).all()
        for row in lst_allergens:
            dct_allergens[row.allergen] = row.key_words
        return dct_allergens

    @staticmethod
    def check_recipe(components, constrains):
        ''' returns the list of constrains the components fits in '''
        allergens = []

        # make a set of unique components
        components_set = set()
        for string in components:
            string = re.split('[^a-z]', string.lower())  # only words remain
            string = list(filter(lambda x: len(x) > 2, string))  # words with >2 letters length remain
            for word in string:
                components_set.add(word)

        #for each allergen iterate through components
        for allergen in constrains.keys():
            for component in components_set:
                if component in constrains[allergen]:
                    allergens.append(allergen)
                    break  #and check next allergen

        return allergens

    def get_top(self, top):
        ''' get top rated recipes'''
        top_recipes = db.session.query(Recipes).order_by(Recipes.rating.desc()).limit(top)
        return top_recipes

    def get_recipe(self, title):
        ''' get a recipe by title and return it as a dict'''
        recipe = db.session.query(Recipes).filter(Recipes.title==title)
        dct = {'title': title,
               'id': recipe.id,
               'ingredients': recipe.ingredients,
               'directions': recipe.directions,
               'rating': rating}
        return dct


def fill_recipes(filename):
    ''' fulfill the recipes table from the given file '''
    with open(filename) as f:
        data = json.load(f)

    titles = set()  #to avoid duplicates
    keys = ['title', 'directions', 'ingredients', 'categories'] # mandatory fields
    for recipe_dct in data:
        # check consistency
        if not recipe_dct or not all([key in recipe_dct.keys() for key in keys]):
            continue
        # check if the recipe is duplicative
        if recipe_dct['title'] in titles:
            continue
        #add to db
        titles.add(recipe_dct['title'])

        # check if it's allergic.
        allergens = Recipes.check_allergies(recipe_dct['ingredients'], recipe_dct['categories'])

        recipe = Recipes(title = recipe_dct['title'],
                         directions = recipe_dct['directions'],
                         ingredients = recipe_dct['ingredients'],
                         categories = recipe_dct['categories'],
                         allergens = allergens,
                         rating=0)
        db.session.add(recipe)
        db.session.commit()


class Allergies(db.Model):

    __tablename__='allergies'

    id = db.Column(db.Integer, primary_key=True)
    allergen = db.Column(db.String(255))
    key_words = db.Column(ScalarListType())


def fill_allergies(filename):
    ''' fulfill the allergies table from the given file '''
    with open(filename) as f:
        data = json.load(f)

    for allergen in data.keys():
        allergy = Allergies(allergen = allergen, key_words = data[allergen])
        db.session.add(allergy)
    db.session.commit()


def db_init(allergo_file, recipes_file):
    ''' initialize a db '''
    db.create_all()
    fill_allergies(allergo_file)
    fill_recipes(recipes_file)

