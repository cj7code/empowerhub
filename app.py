# EmpowerHub Flask Backend - SDG 4, 3, 2 Solution
# Complete backend API with AI integration and database management

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import requests
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_pyfile('config.py')
CORS(app)  # Enable CORS for frontend integration

# Logging setup for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
from config import DATABASE_CONFIG

# =====================================
# DATABASE CONNECTION AND SETUP
# =====================================

def get_db_connection():
    """Establish database connection with error handling"""
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

def init_database():
    """Initialize database tables for EmpowerHub"""
    connection = get_db_connection()
    if not connection:
        logger.error("Failed to connect to database for initialization")
        return False
    
    cursor = connection.cursor()
    
    try:
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS empowerhub_db")
        cursor.execute("USE empowerhub_db")
        
        # Users table for authentication and premium tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                is_premium BOOLEAN DEFAULT FALSE,
                premium_expires DATETIME NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Learning activities table (SDG 4: Education)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                topic VARCHAR(255) NOT NULL,
                level ENUM('beginner', 'intermediate', 'advanced') NOT NULL,
                learning_path TEXT,
                progress INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Question-Answer history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category ENUM('education', 'health', 'nutrition') NOT NULL,
                confidence_score DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Health tracking table (SDG 3: Good Health)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_tracking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                tracking_type ENUM('mental_health', 'wellness', 'symptoms') NOT NULL,
                data JSON NOT NULL,
                mood_score DECIMAL(3,2),
                wellness_score INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Mental health assessments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mental_health_assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                assessment_text TEXT NOT NULL,
                sentiment ENUM('POSITIVE', 'NEGATIVE', 'NEUTRAL') NOT NULL,
                confidence_score DECIMAL(3,2),
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Meal plans table (SDG 2: Zero Hunger)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                ingredients TEXT NOT NULL,
                dietary_restrictions VARCHAR(100),
                meal_plan JSON NOT NULL,
                nutrition_score INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Food waste reduction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_waste_reduction (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                expiring_items TEXT NOT NULL,
                suggestions JSON NOT NULL,
                impact_score INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        connection.commit()
        logger.info("Database initialized successfully")
        return True
        
    except mysql.connector.Error as err:
        logger.error(f"Database initialization error: {err}")
        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()

# =====================================
# AUTHENTICATION HELPERS
# =====================================

def token_required(f):
    """Decorator for protecting routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Remove 'Bearer ' from token
            token = token.split(' ')[1] if token.startswith('Bearer ') else token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# =====================================
# AI INTEGRATION FUNCTIONS
# =====================================

# =====================================
# FREE API FUNCTIONS (NO API KEYS NEEDED)
# =====================================

def get_wikipedia_answer(question):
    """Get answers from Wikipedia API (FREE)"""
    try:
        import urllib.parse
        encoded_question = urllib.parse.quote(question)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_question}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('extract', 'Information not found on Wikipedia')
        return "Could not retrieve information from Wikipedia"
    except Exception as e:
        print(f"Wikipedia API error: {e}")
        return "This is a demo response about educational content."

def get_meal_suggestion(ingredient):
    """Get meal suggestions from TheMealDB (FREE)"""
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('meals'):
                meal = data['meals'][0]
                return f"Try making: {meal['strMeal']} ({meal['strCategory']})"
        return f"No recipes found with {ingredient}"
    except Exception as e:
        print(f"MealDB API error: {e}")
        return f"You can make various dishes with {ingredient}"

def get_random_advice():
    """Get random advice from Advice Slip API (FREE)"""
    try:
        response = requests.get("https://api.adviceslip.com/advice", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['slip']['advice']
        return "Stay positive and take things one day at a time."
    except Exception as e:
        print(f"Advice API error: {e}")
        return "Remember to practice self-care and mindfulness."

# Simple sentiment analysis (no API needed)
def analyze_sentiment(text):
    """Simple sentiment analysis without API"""
    positive_words = ['happy', 'good', 'great', 'excited', 'joy', 'love', 'nice', 'positive', 'awesome', 'fantastic']
    negative_words = ['sad', 'bad', 'angry', 'hate', 'upset', 'stress', 'anxious', 'depress', 'tired', 'worried']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "POSITIVE", 0.7
    elif negative_count > positive_count:
        return "NEGATIVE", 0.7
    else:
        return "NEUTRAL", 0.6

# =====================================
# USER AUTHENTICATION ROUTES
# =====================================

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'User already exists'}), 400
        
        # Create new user
        cursor.execute(
            "INSERT INTO users (email, password_hash, phone) VALUES (%s, %s, %s)",
            (email, password_hash, phone)
        )
        
        user_id = cursor.lastrowid
        connection.commit()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user_id': user_id
        }), 201
        
    except mysql.connector.Error as err:
        logger.error(f"Registration database error: {err}")
        return jsonify({'error': 'Registration failed'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT id, password_hash, is_premium FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user[1], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user[0],
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user_id': user[0],
            'is_premium': user[2]
        }), 200
        
    except mysql.connector.Error as err:
        logger.error(f"Login database error: {err}")
        return jsonify({'error': 'Login failed'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# SDG 4: EDUCATION ROUTES
# =====================================

@app.route('/api/generate-learning-path', methods=['POST'])
@token_required
def generate_learning_path(current_user_id):
    connection = None
    """Generate personalized learning path using AI"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        level = data.get('level', 'beginner')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Create prompt for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an expert educational consultant. Create detailed, practical learning paths."
            },
            {
                "role": "user",
                "content": f"Create a comprehensive learning path for '{topic}' at {level} level. Include specific steps, timeline, resources, and milestones."
            }
        ]
        
        # ✅ USE FREE RESPONSE:
        learning_path = f"Learning Path for {topic}:\n1. Basics\n2. Intermediate\n3. Advanced\n4. Projects\n\nThis is a demo learning path. In production, this would use AI generation."
        
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO learning_activities (user_id, topic, level, learning_path) VALUES (%s, %s, %s, %s)",
            (current_user_id, topic, level, learning_path)
        )
        
        activity_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({
            'success': True,
            'activity_id': activity_id,
            'learning_path': learning_path,
            'topic': topic,
            'level': level
        }), 200
        
    except Exception as e:
        logger.error(f"Learning path generation error: {e}")
        return jsonify({'error': 'Failed to generate learning path'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/answer-question', methods=['POST'])
@token_required
def answer_question(current_user_id):
    connection = None
    try:
        data = request.get_json()
        question = data.get('question')
        context = data.get('context', 'General knowledge and educational content.')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Use FREE Wikipedia API instead of paid APIs
        answer = get_wikipedia_answer(question)
        confidence = 0.85
        
        # Store Q&A in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO qa_history (user_id, question, answer, category, confidence_score) VALUES (%s, %s, %s, %s, %s)",
            (current_user_id, question, answer, 'education', confidence)
        )
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'confidence': round(confidence * 100, 2)
        }), 200
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        return jsonify({'error': 'Failed to answer question'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# SDG 3: HEALTH ROUTES
# =====================================

@app.route('/api/analyze-mental-health', methods=['POST'])
@token_required
def analyze_mental_health(current_user_id):
    connection = None  # Make sure this line is here!
    try:
        data = request.get_json()
        mood_text = data.get('mood_text')
        
        if not mood_text:
            return jsonify({'error': 'Mood text is required'}), 400
        
        # Use our FREE sentiment analysis instead of API
        sentiment, confidence = analyze_sentiment(mood_text)
        
        # Generate recommendations based on sentiment
        recommendations = generate_mental_health_recommendations(sentiment, confidence)
        
        # Add random advice
        advice = get_random_advice()
        recommendations.append(advice)
        
        # Store assessment in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO mental_health_assessments (user_id, assessment_text, sentiment, confidence_score, recommendations) VALUES (%s, %s, %s, %s, %s)",
            (current_user_id, mood_text, sentiment, confidence, json.dumps(recommendations))
        )
        
        assessment_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({
            'success': True,
            'assessment_id': assessment_id,
            'sentiment': sentiment,
            'confidence': round(confidence * 100, 2),
            'recommendations': recommendations,
            'mood_score': calculate_mood_score(sentiment, confidence)
        }), 200
        
    except Exception as e:
        logger.error(f"Mental health analysis error: {e}")
        return jsonify({'error': 'Failed to analyze mental health'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/track-wellness', methods=['POST'])
@token_required
def track_wellness(current_user_id):
    connection = None
    """Track daily wellness metrics"""
    try:
        data = request.get_json()
        sleep_hours = data.get('sleep_hours', 0)
        exercise_minutes = data.get('exercise_minutes', 0)
        water_glasses = data.get('water_glasses', 0)
        
        # Calculate individual scores
        sleep_score = min((sleep_hours / 8) * 100, 100)
        exercise_score = min((exercise_minutes / 30) * 100, 100)
        water_score = min((water_glasses / 8) * 100, 100)
        
        # Calculate overall wellness score
        wellness_score = round((sleep_score + exercise_score + water_score) / 3)
        
        # Prepare wellness data
        wellness_data = {
            'sleep_hours': sleep_hours,
            'exercise_minutes': exercise_minutes,
            'water_glasses': water_glasses,
            'sleep_score': sleep_score,
            'exercise_score': exercise_score,
            'water_score': water_score,
            'overall_score': wellness_score
        }
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO health_tracking (user_id, tracking_type, data, wellness_score) VALUES (%s, %s, %s, %s)",
            (current_user_id, 'wellness', json.dumps(wellness_data), wellness_score)
        )
        
        tracking_id = cursor.lastrowid
        connection.commit()
        
        # Generate wellness recommendations
        recommendations = generate_wellness_recommendations(wellness_score, wellness_data)
        
        return jsonify({
            'success': True,
            'tracking_id': tracking_id,
            'wellness_score': wellness_score,
            'breakdown': wellness_data,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"Wellness tracking error: {e}")
        return jsonify({'error': 'Failed to track wellness'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/health-question', methods=['POST'])
@token_required
def health_question(current_user_id):
    connection = None
    """AI-powered health Q&A system"""
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Create health-focused prompt
        messages = [
            {
                "role": "system",
                "content": "You are a knowledgeable health information assistant. Provide accurate, helpful health information while emphasizing the importance of consulting healthcare professionals. Always include appropriate disclaimers."
            },
            {
                "role": "user",
                "content": f"Health question: {question}"
            }
        ]
        
        # ✅ USE FREE RESPONSE:
        answer = f"Health information about {question}: This is a demo response. Always consult healthcare professionals for medical advice."
        
        # Add standard health disclaimer
        disclaimer = "\n\n⚠️ IMPORTANT: This information is for educational purposes only and should not replace professional medical advice. Always consult with a healthcare provider for medical concerns."
        full_answer = answer + disclaimer
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO qa_history (user_id, question, answer, category, confidence_score) VALUES (%s, %s, %s, %s, %s)",
            (current_user_id, question, full_answer, 'health', 0.9)
        )
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': full_answer,
            'disclaimer': 'Always consult healthcare professionals for medical advice'
        }), 200
        
    except Exception as e:
        logger.error(f"Health question error: {e}")
        return jsonify({'error': 'Failed to answer health question'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# SDG 2: ZERO HUNGER ROUTES
# =====================================

@app.route('/api/generate-meal-plan', methods=['POST'])
@token_required
def generate_meal_plan(current_user_id):
    connection = None
    try:
        data = request.get_json()
        ingredients = data.get('ingredients')
        dietary_restrictions = data.get('dietary_restrictions', 'none')
        
        if not ingredients:
            return jsonify({'error': 'Ingredients are required'}), 400
        
        # Use FREE MealDB API for suggestions
        ingredient_list = [ing.strip() for ing in ingredients.split(',')]
        meal_suggestions = []
        
        for ingredient in ingredient_list[:3]:  # Get suggestions for first 3 ingredients
            suggestion = get_meal_suggestion(ingredient)
            meal_suggestions.append(f"• {suggestion}")
        
        meal_plan_content = "Meal Suggestions:\n" + "\n".join(meal_suggestions)
        meal_plan_content += "\n\nNutrition Tips: Balance your meals with proteins, carbs, and vegetables. Stay hydrated!"
        
        # Calculate nutrition score
        nutrition_score = calculate_nutrition_score(ingredient_list, dietary_restrictions)
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        meal_plan_data = {
            'ingredients': ingredient_list,
            'dietary_restrictions': dietary_restrictions,
            'plan_content': meal_plan_content,
            'nutrition_score': nutrition_score,
            'estimated_cost': estimate_meal_cost(ingredient_list)
        }
        
        cursor.execute(
            "INSERT INTO meal_plans (user_id, ingredients, dietary_restrictions, meal_plan, nutrition_score) VALUES (%s, %s, %s, %s, %s)",
            (current_user_id, ingredients, dietary_restrictions, json.dumps(meal_plan_data), nutrition_score)
        )
        
        plan_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'meal_plan': meal_plan_content,
            'nutrition_score': nutrition_score,
            'ingredients_used': ingredient_list,
            'dietary_restrictions': dietary_restrictions
        }), 200
        
    except Exception as e:
        logger.error(f"Meal plan generation error: {e}")
        return jsonify({'error': 'Failed to generate meal plan'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/reduce-food-waste', methods=['POST'])
@token_required
def reduce_food_waste(current_user_id):
    connection = None
    """Generate suggestions to reduce food waste from expiring items"""
    try:
        data = request.get_json()
        expiring_items = data.get('expiring_items')
        
        if not expiring_items:
            return jsonify({'error': 'Expiring items are required'}), 400
        
        # Create waste reduction prompt
        messages = [
            {
                "role": "system",
                "content": "You are a sustainability expert focused on reducing food waste. Provide creative, practical solutions."
            },
            {
                "role": "user",
                "content": f"These food items are expiring soon: {expiring_items}. Provide creative recipes, preservation methods, and ways to use them before they spoil. Focus on zero waste solutions."
            }
        ]
        
        # ✅ USE FREE RESPONSE:
        suggestions = f"Food waste reduction ideas for {expiring_items}:\n1. Make smoothies\n2. Create soups\n3. Freeze leftovers\n4. Compost scraps"
        
        # Calculate environmental impact score
        item_list = [item.strip() for item in expiring_items.split(',')]
        impact_score = calculate_waste_impact_score(item_list)
        
        # Create suggestions data
        waste_reduction_data = {
            'expiring_items': item_list,
            'suggestions': suggestions,
            'impact_score': impact_score,
            'environmental_benefit': f"Saving {len(item_list)} items from waste reduces carbon footprint by approximately {len(item_list) * 0.5}kg CO2"
        }
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO food_waste_reduction (user_id, expiring_items, suggestions, impact_score) VALUES (%s, %s, %s, %s)",
            (current_user_id, expiring_items, json.dumps(waste_reduction_data), impact_score)
        )
        
        reduction_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({
            'success': True,
            'reduction_id': reduction_id,
            'suggestions': suggestions,
            'impact_score': impact_score,
            'items_saved': len(item_list),
            'environmental_impact': waste_reduction_data['environmental_benefit']
        }), 200
        
    except Exception as e:
        logger.error(f"Food waste reduction error: {e}")
        return jsonify({'error': 'Failed to generate waste reduction suggestions'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/api/nutrition-advice', methods=['POST'])
@token_required
def nutrition_advice(current_user_id):
    connection = None
    """AI-powered nutrition consultation"""
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'Nutrition question is required'}), 400
        
        # Create nutrition-focused prompt
        messages = [
            {
                "role": "system", 
                "content": "You are a qualified nutritionist providing evidence-based nutritional guidance. Focus on scientific accuracy and practical advice."
            },
            {
                "role": "user",
                "content": f"Nutrition question: {question}"
            }
        ]
        
        # ✅ USE FREE RESPONSE:
        advice = f"Nutrition advice about {question}: Focus on balanced meals with proteins, vegetables, and whole grains. Stay hydrated!"
        
        # Add nutrition disclaimer
        disclaimer = "\n\n💡 Note: This nutritional information is for educational purposes. For personalized nutrition advice, consult with a registered dietitian."
        full_advice = advice + disclaimer
        
        # Store in database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO qa_history (user_id, question, answer, category, confidence_score) VALUES (%s, %s, %s, %s, %s)",
            (current_user_id, question, full_advice, 'nutrition', 0.9)
        )
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'question': question,
            'advice': full_advice,
            'disclaimer': 'Consult registered dietitians for personalized nutrition advice'
        }), 200
        
    except Exception as e:
        logger.error(f"Nutrition advice error: {e}")
        return jsonify({'error': 'Failed to provide nutrition advice'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# DASHBOARD AND ANALYTICS ROUTES
# =====================================

@app.route('/api/user-dashboard', methods=['GET'])
@token_required
def user_dashboard(current_user_id):
    """Get user dashboard with analytics and progress"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get user info
        cursor.execute("SELECT email, is_premium, premium_expires, created_at FROM users WHERE id = %s", (current_user_id,))
        user_info = cursor.fetchone()
        
        # Get learning activities count
        cursor.execute("SELECT COUNT(*) FROM learning_activities WHERE user_id = %s", (current_user_id,))
        learning_count = cursor.fetchone()[0]
        
        # Get health tracking count
        cursor.execute("SELECT COUNT(*) FROM health_tracking WHERE user_id = %s", (current_user_id,))
        health_count = cursor.fetchone()[0]
        
        # Get meal plans count
        cursor.execute("SELECT COUNT(*) FROM meal_plans WHERE user_id = %s", (current_user_id,))
        meal_plans_count = cursor.fetchone()[0]
        
        # Get food waste reduction count
        cursor.execute("SELECT COUNT(*) FROM food_waste_reduction WHERE user_id = %s", (current_user_id,))
        waste_reduction_count = cursor.fetchone()[0]
        
        # Get average wellness score
        cursor.execute("SELECT AVG(wellness_score) FROM health_tracking WHERE user_id = %s AND wellness_score IS NOT NULL", (current_user_id,))
        avg_wellness_score = cursor.fetchone()[0] or 0
        
        # Get recent learning activities
        cursor.execute("SELECT topic, level, progress, created_at FROM learning_activities WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (current_user_id,))
        recent_learning = cursor.fetchall()
        
        # Get recent health assessments
        cursor.execute("SELECT tracking_type, wellness_score, created_at FROM health_tracking WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (current_user_id,))
        recent_health = cursor.fetchall()
        
        # Format the dashboard data
        dashboard_data = {
            'user_info': {
                'email': user_info[0],
                'is_premium': bool(user_info[1]),
                'premium_expires': user_info[2].isoformat() if user_info[2] else None,
                'member_since': user_info[3].isoformat()
            },
            'activity_counts': {
                'learning_activities': learning_count,
                'health_tracking': health_count,
                'meal_plans': meal_plans_count,
                'waste_reduction': waste_reduction_count
            },
            'wellness_score': round(float(avg_wellness_score), 2),
            'recent_activities': [
                {
                    'topic': activity[0],
                    'level': activity[1],
                    'progress': activity[2],
                    'date': activity[3].isoformat()
                } for activity in recent_learning
            ],
            'recent_health': [
                {
                    'type': activity[0],
                    'score': activity[1],
                    'date': activity[2].isoformat()
                } for activity in recent_health
            ],
            'sdg_progress': {
                'education': calculate_education_progress(current_user_id, cursor),
                'health': calculate_health_progress(current_user_id, cursor),
                'nutrition': calculate_nutrition_progress(current_user_id, cursor)
            }
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# HELPER FUNCTIONS
# =====================================

def generate_mental_health_recommendations(sentiment, confidence):
    """Generate personalized mental health recommendations"""
    recommendations = {
        'POSITIVE': [
            "Keep up the positive mindset with regular exercise and social connections",
            "Practice gratitude and maintain your current healthy habits",
            "Consider sharing your positivity with others who might need support"
        ],
        'NEGATIVE': [
            "Consider talking to a trusted friend, family member, or mental health professional",
            "Try relaxation techniques like deep breathing or meditation",
            "Engage in physical activity, even a short walk can help improve mood",
            "Ensure you're getting adequate sleep and nutrition"
        ],
        'NEUTRAL': [
            "Engage in activities that bring you joy and fulfillment",
            "Connect with friends and family for social support",
            "Try mindfulness or meditation practices",
            "Consider exploring new hobbies or interests"
        ]
    }
    
    return recommendations.get(sentiment, recommendations['NEUTRAL'])

def calculate_mood_score(sentiment, confidence):
    """Calculate mood score from sentiment analysis"""
    base_scores = {'POSITIVE': 85, 'NEUTRAL': 60, 'NEGATIVE': 35}
    base_score = base_scores.get(sentiment, 60)
    
    # Adjust based on confidence
    confidence_adjustment = (confidence - 0.5) * 20
    return max(10, min(100, base_score + confidence_adjustment))

def generate_wellness_recommendations(wellness_score, wellness_data):
    """Generate personalized wellness recommendations"""
    recommendations = []
    
    if wellness_data['sleep_score'] < 70:
        recommendations.append("Aim for 7-9 hours of quality sleep each night")
    
    if wellness_data['exercise_score'] < 70:
        recommendations.append("Try to get at least 30 minutes of physical activity daily")
    
    if wellness_data['water_score'] < 70:
        recommendations.append("Increase water intake to 8 glasses per day")
    
    if wellness_score >= 80:
        recommendations.append("Great job maintaining excellent wellness habits!")
    elif wellness_score >= 60:
        recommendations.append("You're on the right track - small improvements can make a big difference")
    else:
        recommendations.append("Focus on gradual improvements in sleep, exercise, and hydration")
    
    return recommendations

def calculate_nutrition_score(ingredients, dietary_restrictions):
    """Calculate nutrition score based on ingredient variety and dietary considerations"""
    base_score = min(len(ingredients) * 10, 100)  # More variety = higher score
    
    # Bonus points for healthy ingredients
    healthy_ingredients = ['vegetables', 'fruits', 'whole grains', 'lean protein', 'legumes']
    bonus = sum(5 for ingredient in ingredients if any(healthy in ingredient.lower() for healthy in healthy_ingredients))
    
    return min(100, base_score + bonus)

def estimate_meal_cost(ingredients):
    """Estimate meal cost based on ingredients (simplified calculation)"""
    # Average cost per ingredient in KES
    avg_cost_per_ingredient = 50
    return len(ingredients) * avg_cost_per_ingredient

def calculate_waste_impact_score(items):
    """Calculate environmental impact score for waste reduction"""
    # Each item saved contributes to environmental score
    return min(100, len(items) * 15)

def calculate_education_progress(user_id, cursor):
    """Calculate education progress based on learning activities"""
    cursor.execute("SELECT COUNT(*), AVG(progress) FROM learning_activities WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    activity_count = result[0] or 0
    avg_progress = result[1] or 0
    
    return {
        'total_activities': activity_count,
        'average_progress': round(float(avg_progress), 2),
        'level': determine_education_level(activity_count, avg_progress)
    }

def calculate_health_progress(user_id, cursor):
    """Calculate health progress based on wellness tracking"""
    cursor.execute("SELECT COUNT(*), AVG(wellness_score) FROM health_tracking WHERE user_id = %s AND wellness_score IS NOT NULL", (user_id,))
    result = cursor.fetchone()
    tracking_count = result[0] or 0
    avg_score = result[1] or 0
    
    return {
        'tracking_sessions': tracking_count,
        'average_score': round(float(avg_score), 2),
        'status': determine_health_status(avg_score)
    }

def calculate_nutrition_progress(user_id, cursor):
    """Calculate nutrition progress based on meal plans and waste reduction"""
    cursor.execute("SELECT COUNT(*), AVG(nutrition_score) FROM meal_plans WHERE user_id = %s", (user_id,))
    meal_result = cursor.fetchone()
    meal_count = meal_result[0] or 0
    avg_nutrition = meal_result[1] or 0
    
    cursor.execute("SELECT COUNT(*), AVG(impact_score) FROM food_waste_reduction WHERE user_id = %s", (user_id,))
    waste_result = cursor.fetchone()
    waste_count = waste_result[0] or 0
    avg_impact = waste_result[1] or 0
    
    return {
        'meal_plans': meal_count,
        'waste_reduction_actions': waste_count,
        'average_nutrition_score': round(float(avg_nutrition), 2),
        'average_impact_score': round(float(avg_impact), 2)
    }

def determine_education_level(activity_count, avg_progress):
    """Determine education level based on activity count and progress"""
    if activity_count == 0:
        return "Beginner"
    elif activity_count < 5:
        return "Explorer"
    elif activity_count < 10:
        return "Learner"
    elif activity_count < 20:
        return "Scholar"
    else:
        return "Expert"

def determine_health_status(avg_score):
    """Determine health status based on average wellness score"""
    if avg_score >= 80:
        return "Excellent"
    elif avg_score >= 60:
        return "Good"
    elif avg_score >= 40:
        return "Fair"
    else:
        return "Needs Improvement"

def format_edamam_recipes(recipes):
    """Format Edamam API recipes into a readable meal plan"""
    if not recipes:
        return "No recipes found with the provided ingredients."
    
    meal_plan = "Here are some recipe suggestions based on your ingredients:\n\n"
    
    for i, recipe in enumerate(recipes[:3]):  # Show top 3 recipes
        recipe_data = recipe.get('recipe', {})
        meal_plan += f"{i+1}. {recipe_data.get('label', 'Unknown Recipe')}\n"
        meal_plan += f"   Calories: {round(recipe_data.get('calories', 0))} kcal\n"
        meal_plan += f"   Servings: {recipe_data.get('yield', 1)}\n"
        meal_plan += f"   URL: {recipe_data.get('url', '#')}\n\n"
    
    return meal_plan

# =====================================
# ADDITIONAL UTILITY ROUTES
# =====================================

@app.route('/api/user-history/<category>', methods=['GET'])
@token_required
def get_user_history(current_user_id, category):
    """Get user history for a specific category"""
    try:
        valid_categories = ['education', 'health', 'nutrition']
        if category not in valid_categories:
            return jsonify({'error': 'Invalid category'}), 400
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if category == 'education':
            cursor.execute("""
                SELECT question, answer, confidence_score, created_at 
                FROM qa_history 
                WHERE user_id = %s AND category = 'education'
                ORDER BY created_at DESC
                LIMIT 20
            """, (current_user_id,))
        elif category == 'health':
            cursor.execute("""
                SELECT tracking_type, wellness_score, created_at 
                FROM health_tracking 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (current_user_id,))
        else:  # nutrition
            cursor.execute("""
                SELECT ingredients, nutrition_score, created_at 
                FROM meal_plans 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (current_user_id,))
        
        history = cursor.fetchall()
        
        # Format history based on category
        formatted_history = []
        for item in history:
            if category == 'education':
                formatted_history.append({
                    'question': item[0],
                    'answer': item[1],
                    'confidence': item[2],
                    'date': item[3].isoformat()
                })
            elif category == 'health':
                formatted_history.append({
                    'type': item[0],
                    'score': item[1],
                    'date': item[2].isoformat()
                })
            else:  # nutrition
                formatted_history.append({
                    'ingredients': item[0],
                    'nutrition_score': item[1],
                    'date': item[2].isoformat()
                })
        
        return jsonify({
            'success': True,
            'category': category,
            'history': formatted_history
        }), 200
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({'error': 'Failed to retrieve history'}), 500
    
    finally:
        if connection:
            cursor.close()
            connection.close()

# =====================================
# APPLICATION INITIALIZATION
# =====================================

@app.route('/')
def index():
    """Root endpoint with API information"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'EmpowerHub API is running',
        'version': '1.0',
        'sdgs_supported': ['SDG 2: Zero Hunger', 'SDG 3: Good Health', 'SDG 4: Quality Education']
    })

if __name__ == '__main__':
    # Initialize database on startup
    if init_database():
        logger.info("Starting EmpowerHub Flask Server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to initialize database. Server not started.")