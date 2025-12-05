import random
import logging

logger = logging.getLogger(__name__)

def get_topic_questions_for_module(module_id, mysql):
    """
    Get topic quiz questions for a specific module.
    
    Args:
        module_id (int): The ID of the module
        mysql: Database connection object
        
    Returns:
        list: List of questions for the module
    """
    try:
        connection = mysql.get_connection()
        if connection is None:
            logger.error("Database connection not available")
            return []
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option
            FROM topic_quiz_questions 
            WHERE module_id = %s
            ORDER BY id
        """, (module_id,))
        
        questions = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Convert to list of dictionaries if needed
        if isinstance(questions, tuple):
            questions = list(questions)
        elif questions is None:
            questions = []
            
        logger.info(f"Retrieved {len(questions)} questions for module {module_id}")
        return questions
        
    except Exception as e:
        logger.error(f"Error getting topic questions for module {module_id}: {e}")
        return []

def get_random_topic_questions(module_id, count, mysql):
    """
    Get a random selection of topic quiz questions for a module.
    
    Args:
        module_id (int): The ID of the module
        count (int): Number of questions to return
        mysql: Database connection object
        
    Returns:
        list: Randomly selected questions
    """
    try:
        questions = get_topic_questions_for_module(module_id, mysql)
        
        # If we have fewer questions than requested, return all of them
        if len(questions) <= count:
            return questions
            
        # Otherwise, randomly select the requested number
        return random.sample(questions, count)
        
    except Exception as e:
        logger.error(f"Error getting random topic questions for module {module_id}: {e}")
        return []

def save_topic_quiz_attempt(user_id, module_id, course_id, answers, mysql):
    """
    Save a topic quiz attempt and calculate results.
    
    Args:
        user_id (int): The ID of the user
        module_id (int): The ID of the module
        course_id (int): The ID of the course
        answers (dict): Dictionary of question_id -> selected_option
        mysql: Database connection object
        
    Returns:
        int: The attempt ID, or None if failed
    """
    try:
        connection = mysql.get_connection()
        if connection is None:
            logger.error("Database connection not available")
            return None
            
        cursor = connection.cursor()
        
        # Start transaction
        connection.start_transaction()
        
        # Create the quiz attempt record
        cursor.execute("""
            INSERT INTO topic_quiz_attempts (user_id, module_id, course_id)
            VALUES (%s, %s, %s)
        """, (user_id, module_id, course_id))
        
        attempt_id = cursor.lastrowid
        
        # Save each answer
        for question_id, selected_option in answers.items():
            # Get the correct answer and option texts for this question
            cursor.execute("""
                SELECT correct_option, option_a, option_b, option_c, option_d 
                FROM topic_quiz_questions WHERE id = %s
            """, (question_id,))
            
            result = cursor.fetchone()
            if result:
                correct_option = result[0] if isinstance(result, tuple) else result.get('correct_option')
                is_correct = (selected_option.upper() == correct_option.upper())
                
                # Save the answer
                cursor.execute("""
                    INSERT INTO topic_quiz_answers (attempt_id, question_id, selected_option, is_correct)
                    VALUES (%s, %s, %s, %s)
                """, (attempt_id, question_id, selected_option, is_correct))
        
        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f"Saved topic quiz attempt {attempt_id} for user {user_id}")
        return attempt_id
        
    except Exception as e:
        logger.error(f"Error saving topic quiz attempt: {e}")
        # Rollback transaction if it exists
        try:
            if connection:
                connection.rollback()
                connection.close()
        except:
            pass
        return None

def get_topic_quiz_results(attempt_id, mysql):
    """
    Get the results for a topic quiz attempt.
    
    Args:
        attempt_id (int): The ID of the attempt
        mysql: Database connection object
        
    Returns:
        dict: Results including score, total questions, and individual answers
    """
    try:
        connection = mysql.get_connection()
        if connection is None:
            logger.error("Database connection not available")
            return {}
            
        cursor = connection.cursor(dictionary=True)
        
        # Get the attempt details
        cursor.execute("""
            SELECT tqa.*, cm.title as module_title, c.title as course_title
            FROM topic_quiz_attempts tqa
            JOIN course_modules cm ON tqa.module_id = cm.id
            JOIN courses c ON tqa.course_id = c.id
            WHERE tqa.id = %s
        """, (attempt_id,))
        
        attempt = cursor.fetchone()
        
        if not attempt:
            cursor.close()
            connection.close()
            return {}
        
        # Get the answers for this attempt with question details
        cursor.execute("""
            SELECT qa.*, tq.question_text, tq.correct_option, 
                   tq.option_a, tq.option_b, tq.option_c, tq.option_d
            FROM topic_quiz_answers qa
            JOIN topic_quiz_questions tq ON qa.question_id = tq.id
            WHERE qa.attempt_id = %s
            ORDER BY qa.id
        """, (attempt_id,))
        
        answers = cursor.fetchall()
        
        # Calculate score
        total_questions = len(answers)
        correct_answers = sum(1 for answer in answers if 
                            (answer.get('is_correct') if isinstance(answer, dict) else answer[7]))
        
        # Calculate percentage
        percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        cursor.close()
        connection.close()
        
        results = {
            'attempt': attempt,
            'answers': answers,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': percentage,
            'passed': percentage >= 70  # 70% to pass
        }
        
        logger.info(f"Retrieved quiz results for attempt {attempt_id}: {correct_answers}/{total_questions}")
        return results
        
    except Exception as e:
        logger.error(f"Error getting topic quiz results for attempt {attempt_id}: {e}")
        return {}

def has_user_completed_topic_quiz(user_id, module_id, mysql):
    """
    Check if a user has completed the topic quiz for a module.
    
    Args:
        user_id (int): The ID of the user
        module_id (int): The ID of the module
        mysql: Database connection object
        
    Returns:
        bool: True if user has completed the quiz, False otherwise
    """
    try:
        connection = mysql.get_connection()
        if connection is None:
            logger.error("Database connection not available")
            return False
            
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM topic_quiz_attempts 
            WHERE user_id = %s AND module_id = %s
        """, (user_id, module_id))
        
        result = cursor.fetchone()
        count = result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0)
        
        cursor.close()
        connection.close()
        
        return count > 0
        
    except Exception as e:
        logger.error(f"Error checking if user {user_id} completed quiz for module {module_id}: {e}")
        return False

def unlock_next_module(user_id, course_id, current_module_id, mysql):
    """
    Unlock the next module in a course after completing a quiz.
    
    Args:
        user_id (int): The ID of the user
        course_id (int): The ID of the course
        current_module_id (int): The ID of the completed module
        mysql: Database connection object
    """
    try:
        connection = mysql.get_connection()
        if connection is None:
            logger.error("Database connection not available")
            return
            
        cursor = connection.cursor()
        
        # Get the current module's order index
        cursor.execute("""
            SELECT order_index FROM course_modules WHERE id = %s
        """, (current_module_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            connection.close()
            return
            
        current_order = result[0] if isinstance(result, tuple) else result.get('order_index')
        
        # Get the next module
        cursor.execute("""
            SELECT id FROM course_modules 
            WHERE course_id = %s AND order_index = %s
        """, (course_id, current_order + 1))
        
        next_module = cursor.fetchone()
        if not next_module:
            cursor.close()
            connection.close()
            return
            
        next_module_id = next_module[0] if isinstance(next_module, tuple) else next_module.get('id')
        
        # Mark the next module as unlocked (this would depend on how your system tracks locked/unlocked status)
        # For now, we'll just log that the next module should be unlocked
        logger.info(f"Next module {next_module_id} should be unlocked for user {user_id}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"Error unlocking next module for user {user_id}: {e}")

# Additional helper functions can be added here as needed