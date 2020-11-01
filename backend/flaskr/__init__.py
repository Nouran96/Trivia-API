import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
CURRENT_CATEGORY = None

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  CURRENT_CATEGORY = Category.query.first().type
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={r"*/*": {"origins": "*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')

    return response

  '''
  Paginate Questions
  '''
  def paginate_questions(request, questions):
    page = request.args.get('page', 1, type=int)
    start =  (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in questions]
    current_questions = questions[start:end]

    return current_questions

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  @cross_origin()
  def get_categories():
    categories = Category.query.order_by(Category.id).all()

    return jsonify({
      'success': True,
      'categories': {category.id: category.type for category in categories}
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  @cross_origin()
  def get_paginated_questions():

    questions = Question.query.order_by(Question.id).all()
    categories = Category.query.order_by(Category.id).all()
    current_questions = paginate_questions(request, questions)

    if len(current_questions) == 0:
      abort(404, 'not found')

    return jsonify({
      "questions": current_questions,
      "total_questions": len(questions),
      "categories": {category.id: category.type for category in categories},
      "current_category": CURRENT_CATEGORY,
      "success": True
    })

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  @cross_origin()
  def delete_question(question_id):
    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question is None:
      abort(404)

    question.delete()

    return jsonify({
      "success": True,
      "deleted": question_id
    })

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  @app.route('/questions', methods=['POST'])
  @cross_origin()
  def add_question():
    body = request.get_json()

    search_term = body.get('searchTerm', None)

    question = body.get('question', None)
    answer = body.get('answer', None)
    difficulty = body.get('difficulty', None)
    category = body.get('category', None)

    if search_term is None:
      try:
        question = Question(question=question, answer=answer, difficulty=difficulty, category=category)
        question.insert()

        return jsonify({
          "success": True,
          "created": question.id
        })

      except:
        abort(422)

    else:
      questions = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search_term)))
      categories = Category.query.all()

      return jsonify({
        "questions": paginate_questions(request, questions),
        "total_questions": len(Question.query.all()),
        "current_category": CURRENT_CATEGORY,
        "success": True
      })

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  @cross_origin()
  def get_questions_by_category(category_id):

    current_category = Category.query.filter(Category.id == category_id).one_or_none()

    if current_category is None:
      abort(404)
    
    else:
      questions = Question.query.filter(Question.category == category_id)

      CURRENT_CATEGORY = current_category.type

      return jsonify({
        "questions": paginate_questions(request, questions),
        "total_questions": len(Question.query.all()),
        "current_category": CURRENT_CATEGORY
      })


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  @cross_origin()
  def get_quiz_questions():
    body = request.get_json()

    previous_questions = body.get('previous_questions', None)
    quiz_category = body.get('quiz_category', None)

    current_question = None

    # If no category is specified
    if quiz_category.get('id') == 0:
      # If first question
      if len(previous_questions) == 0:
        current_question = Question.query.order_by(func.random()).first()

      else:
        random_questions = Question.query.order_by(func.random())

        for question in random_questions:
          if question.id in previous_questions:
            continue
          else:
            current_question = question

    else:
      if len(previous_questions) == 0:
        current_question = Question.query.order_by(func.random()).filter(Question.category == quiz_category.get('id')).first()

      else:
        random_questions = Question.query.order_by(func.random()).filter(Question.category == quiz_category.get('id'))

        for question in random_questions:
          if question.id in previous_questions:
            continue
          else:
            current_question = question
    
    return jsonify({
      "question": None if current_question is None else current_question.format(),
      "success": True
    })

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  @cross_origin()
  def not_found(error):
    return jsonify({
      "error": 404,
      "success": False,
      "message": "Resource Not Found"
    }), 404

  @app.errorhandler(422)
  @cross_origin()
  def unprocessable(error):
    return jsonify({
      "error": 422,
      "success": False,
      "message": "Unprocessable Request"
      }), 422

  @app.errorhandler(400)
  @cross_origin()
  def bad_request(error):
    return jsonify({
      "error": 400,
      "success": False,
      "message": "Bad Request"
    }), 400

  @app.errorhandler(500)
  @cross_origin()
  def internal_server_error(error):
    return jsonify({
      "error": 500,
      "success": False,
      "message": "Internal Server Error"
    }), 500
  
  return app

    