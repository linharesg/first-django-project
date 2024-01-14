from django.test import TestCase
import datetime
from django.utils import timezone
from django.urls import reverse
from .models import Question, Choice
import random
import html
class QuestionModelTests(TestCase):
    
    def test_was_puclished_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date is in the future.
        """
        
        time = timezone.now() + datetime.timedelta(days = 30)
        future_question = Question(pub_date = time)

        self.assertIs(future_question.was_published_recently(), False)
        
    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions shose pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date = time)
        self.assertIs(old_question.was_published_recently(), False)
        
    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date is within the laste day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)
        
        
def create_question(question_text, days):
    """
    Create a question with the given 'question_text' and publish the given number of 'days' offset
    to now (negative for questions published in the past, positive for questions that have yest to be published).
    """
    
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text = question_text, pub_date = time)

def create_choice(question: Question):
    """
    Create a choice to any given Question, with a static text and 0 default votes.
    """
    return question.choice_set.create(choice_text = "This is a choice.", votes = 0)

class QuestionIndexViewTests(TestCase):
    
    def test_no_questions(self):
        """
        If there is no questions, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Quesitons with a pub_date in the past are displayed on the index page.
        """
        question = create_question(question_text="Past question", days=-30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"], [question],
        )
        
    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )
        
class QuestionDetailViewTests(TestCase):
    
    def test_future_question(self):
        """
        There is to page no be loaded for questions with pub_date in the future, resulting in a 404 error. 
        """
        future_question = create_question(question_text ="This is a poll from the future", days = 30)
        url = reverse("polls:detail", args = (future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_past_question(self):
        """
        Display a page to the details of a qustion made in the past
        """
        past_question = create_question(question_text = "This is a past question", days = -5)
        url = reverse("polls:detail", args = (past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, past_question.question_text)
        
    def test_question_with_many_choices(self):
        """
        The question detail page displays all the choices for a quesiton made in the past.
        """
        past_question = create_question(question_text = "This is a past question", days = -5)
          
        NUMBER_OF_CHOICES = 10
        
        for i in range(NUMBER_OF_CHOICES):
            create_choice(past_question)

        url = reverse("polls:detail", args = (past_question.id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        [self.assertContains(response, past_question.choice_set.all()[choice_index].choice_text) for choice_index in range(NUMBER_OF_CHOICES)]
        
    def test_vote_submission(self):
        """
        Vote in a choice redirects to the vote page and increase the count of votes to the choice voted.
        """
        past_question = create_question(question_text="This is a question in the past.", days=-2)
        create_choice(past_question)

        url = reverse("polls:vote", args = (past_question.id,))
        response = self.client.post(url, {"choice": past_question.choice_set.first().id})

        self.assertEqual(response.status_code, 302)

        updated_choice_count = past_question.choice_set.first().votes
        self.assertEqual(updated_choice_count, 1)

    def test_vote_submission_with_many_choices(self):
        """
        Vote in a random choice, redirecting to the vote page and increasing the votes to the choice voted.
        """
        past_question = create_question(question_text="This is a question in the past.", days=-2)
        
        NUMBER_OF_CHOICES = 10
        for i in range(NUMBER_OF_CHOICES):
            create_choice(past_question)

        random_choice_id = random.choice(past_question.choice_set.all()).id

        url = reverse("polls:vote", args = (past_question.id,))
        response = self.client.post(url, {"choice": random_choice_id})
        self.assertEqual(response.status_code, 302)

        updated_choice_count = past_question.choice_set.get(pk=random_choice_id).votes
        self.assertEqual(updated_choice_count, 1)
        
    def test_vote_submission_without_select_choice(self):
        """
        Display a error message in the detail view when voting without chosing a choice (no arguments given in post method)
        """
        past_question = create_question(question_text="This is a question.", days=-2)
        create_choice(past_question)

        url = reverse("polls:vote", args=(past_question.id,))
        response = self.client.post(url, {})

        decoded_response = html.unescape(response.content.decode())
        self.assertIn("You didn't select a choice.", decoded_response)

