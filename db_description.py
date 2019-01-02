#!/usr/bin/python3
import json
import flask
import sqlalchemy
from sqlalchemy_utils import PasswordType, ScalarListType

# Describe database structure
class Users(db.Model):

    __tablename__ = "users"

    login = db.Column(db.String(4096), primary_key=True)
    name = db.Column(db.String(4096))
    favorites = db.Column(ScalarListType(db.Integer))  #list of recipes' id
    allergies = db.Column(ScalarListType()) #list of user's allergies

    password = db.Column(
        PasswordType(
            # The returned dictionary is forwarded to the CryptContext
            onload=lambda **kwargs: dict(
                schemes=flask.current_app.config['PASSWORD_SCHEMES'],
                **kwargs
            ),
        ),
        unique=False,
        nullable=False,
    )

    def search_recipes(self):
        ''' search recipes based on conditions and return a list of id '''
        pass

    def get_favorites(self):
        ''' get the user's favorites and return the list of id '''
        pass

    def get_top(self):
        ''' get top rated recipes'''
        pass

    def vote(self, value, recipe_id):
        ''' if not none, send to function makes change in recipe'''
        pass


class Recipes(db.Model, Allergies):

    __tablename__='recipes'

    id = db.Column(db.Integer, primary_key=True)
    directions = db.Column(db.String(4096))
    title = db.Column(db.String(4096))
    ingredients = db.Column(ScalarListType())
    categories = db.Column(ScalarListType())
    rating = db.Column(db.Integer)

    def check_allergies(self):
        ''' returns the list of allergens based on ingredients and categories'''
        allergens = []

        #get allergens from db table 'Allergies'
   #!!!!!!!!!!     dct_all = get_allergens()

        # check if there are allergens and make a list
        allergens.extend(check_recipe(ingredients, dct_all))
        allergens.extend(check_recipe(categories, dct_all))

        return allergens


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
                    break

        return allergens


class Allergies(db.Model):

    __tablename__='allergies'

    id = db.Column(db.Integer, primary_key=True)
    allergen = db.Column(db.String)
    key_words = db.Column(ScalarListType())


class Recipes_Allerg(db.Model):

    __tablename__='recipes_allergies'

    recipe_id = db.Column(db.Integer, ForeignKey='recipes.id')
    allergen = db.Column(db.Integer, ForeignKey='allergies.id')


class Fill_Model(db.Model):

    def fill_recipes(self, filename):
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
            recipe = Recipes(title = recipe_dct['title'],
                             directions = recipe_dct['directions'],
                             ingredients = recipe_dct['ingredients'],
                             categories = recipe_dct['categories'],
                             rating=0)
            db.session.add(recipe)
            #check if it's allergic
            if recipe.check_allergies():
    #!!!!!!!!!!            put_to_rec_all(recipe.title, recipe.check_allergies())
        db.session.commit()



    def fill_allergies(self, filename):
        ''' fulfill the allergies table from the given file '''
        with open(filename) as f:
            data = json.load(f)

        for allergen in data.keys():
            allergy = Allergies(allergen = allergen, key_words = data[allergen])
            db.session.add(allergy)
        db.session.commit()


    def fill_recipes_allergies(self):
        pass

db.create_all()

