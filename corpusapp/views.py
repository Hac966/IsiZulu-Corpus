from django.shortcuts import render, redirect, get_object_or_404
from .models import Entry, HistoryBase, CeremoniesBase, AttireBase, CuisineBase, UserInfo, QuizBase, QuizScores, WordFrequency
from django.contrib import messages
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import UserRegisterForm
from django.db.models import Count, Avg
import re
from collections import Counter
from django.db.models import Sum, Avg, F
from django.db.models.functions import Length
import json
import os
from django.views.decorators.csrf import csrf_exempt # Temporarily for testing AJAX
from google import genai
from google.genai.errors import APIError
from django.http import JsonResponse

# Create your views here.
def home(request):
    return render(request, 'home.html')

def cuisine(request):
    bases = CuisineBase.objects.filter(status="Approved")
    return render(request, 'cuisine.html', {'cuisines': bases})

def ceremonies(request):
    bases = CeremoniesBase.objects.filter(status="Approved")
    return render(request, 'ceremonies.html', {"ceremonies": bases})

def attire(request):
    bases = AttireBase.objects.filter(status="Approved")
    return render(request, 'attire.html', {'attires': bases})

def history(request):
    bases = HistoryBase.objects.filter(status="Approved")
    return render(request, 'history.html', {"histories": bases})


def quizz(request):
    MAX_QUESTIONS = 10
    should_reset = request.session.get('quiz_finished', False) or 'reset' in request.GET

    if 'quiz_questions' not in request.session or should_reset:
        all_questions = list(
            QuizBase.objects.filter(status="Approved")
            .order_by('?')[:MAX_QUESTIONS]
            .values('id', 'question', 'answer')
        )

        request.session['quiz_questions'] = all_questions
        request.session['current_q_index'] = 0
        request.session['score'] = 0
        request.session['quiz_finished'] = False
        request.session.modified = True

        if 'reset' in request.GET:
            return redirect('quizz')

    quiz_questions = request.session.get('quiz_questions', [])
    current_q_index = request.session.get('current_q_index', 0)
    score = request.session.get('score', 0)
    actual_max_questions = min(MAX_QUESTIONS, len(quiz_questions))

    if request.method == 'POST' and current_q_index < actual_max_questions:
        user_answer = request.POST.get('userAnswer', '').strip().lower()
        current_question_data = quiz_questions[current_q_index]
        correct_answer = str(current_question_data.get('answer', '')).strip().lower()

        if user_answer == correct_answer:
            request.session['score'] += 1
            messages.success(request, "Correct!")
        else:
            messages.error(request, f"Wrong. The answer was: {current_question_data['answer']}")

        request.session['current_q_index'] += 1
        request.session.modified = True
        return redirect('quizz')

    if current_q_index >= actual_max_questions:

        if not request.session.get('quiz_finished', False) and request.user.is_authenticated:
            try:
                QuizScores.objects.create(
                    user=request.user,
                    score=score,
                    max_score=actual_max_questions
                )
                messages.info(request, "Your score has been saved! 💾")
            except Exception as e:
                print(f"Error saving quiz score: {e}")
                messages.warning(request, "Could not save your score.")
        request.session['quiz_finished'] = True
        context = {
            'quiz_finished': True,
            'final_score': score,
            'max_score': actual_max_questions
        }
    elif len(quiz_questions) > 0:
        current_question_data = quiz_questions[current_q_index]
        context = {
            'quiz_finished': False,
            'current_question_number': current_q_index + 1,
            'question': current_question_data['question'],
            'score': score,
            'max_questions': actual_max_questions
        }
    else:
        context = {
            'quiz_finished': True,
            'final_score': 0,
            'max_score': 0,
            'no_questions': True
        }

    return render(request, 'quizz.html', context)

@login_required
def addEntry(request):
    if request.method == 'POST':
        zulu_phrase_data = request.POST.get('zulu-phrase')
        english_translation_data = request.POST.get('english-translation')
        isixhosa_translation_data = request.POST.get('isixhosa-translation')
        isipedi_translation_data = request.POST.get('isipedi-translation')
        extract_data = request.POST.get('extract')
        commonly_data = request.POST.get('commonly')
        word_usage_data = request.POST.get('word-usage')
        learn_more_data = request.POST.get('learnMore')

        try:
            Entry.objects.create(
                isizulu = zulu_phrase_data,
                english = english_translation_data,
                isixhosa = isixhosa_translation_data,
                isipedi = isipedi_translation_data,
                extract = extract_data,
                commonly = commonly_data,
                word_usage = word_usage_data,
                learn_more = learn_more_data,
                user = request.user
            )
            messages.success(request, "Entry successfully created!")

        except Exception as e:
            messages.error(request, f"Failed to create entry: {e}")

        return redirect('home')
    return render(request, 'addEntry.html')

def stats(request):
    return render(request, 'stats.html')


def entry(request):
    if request.method == 'POST':
        searched = request.POST.get("search-bar")
        if searched:
            entries_to_update = Entry.objects.filter(status='Approved').filter(
                Q(english__icontains=searched) | Q(isizulu__icontains=searched)
            )
            entries_to_update.update(word_frequency=F('word_frequency') + 1)
            redirect_url = f'/entry/?q={searched}'
            return redirect(redirect_url)
        else:
            return redirect('home')
    searched = request.GET.get("q")
    entries = []
    word_freq_dict = {
        item.word: item.count
        for item in WordFrequency.objects.all()
    }

    if searched:
        matched_entries = Entry.objects.filter(status='Approved').filter(
            Q(english__icontains=searched) | Q(isizulu__icontains=searched)
        )[:3]
        for entry_obj in matched_entries:
            entry_word_freqs = []

            if entry_obj.isizulu:
                text = entry_obj.isizulu.lower()

                words = set(re.findall(r'\b\w+\b', text))

                for word in words:
                    count = word_freq_dict.get(word, 0)

                    if count > 0:
                        entry_word_freqs.append((word, count))
            entry_obj.db_word_frequencies = entry_word_freqs

        entries = matched_entries
    word_list = WordFrequency.objects.all()[:100]
    total_unique_words = WordFrequency.objects.count()

    return render(request, 'entry.html', {
        'searched': searched,
        'entries': entries,
        'word_list': word_list,
        'total_unique_words': total_unique_words
    })

@login_required
def addHistory(request):
    if request.method == 'POST':
        heading_data = request.POST.get('headingForHistory')
        extract_data = request.POST.get('extractForHistory')
        picture_file = request.FILES.get('ImageForHistory')
        file_data = request.FILES.get('fileForHistory')


        story = HistoryBase(
            heading = heading_data,
            extract = extract_data,
            picture = picture_file,
            file = file_data,
            user=request.user
        )
        story.save()
        messages.success(request, "Post created successfully!")
        return redirect('home')

    return render(request, 'addHistory.html')

@login_required
def addCuisine(request):
    if request.method == 'POST':
        heading_data = request.POST.get('headingForCuisine')
        extract_data = request.POST.get('extractForCuisine')
        picture_data = request.FILES.get('imageForCuisine')
        learn_more_data = request.POST.get('learnMore')
        file_data = request.FILES.get('fileForCuisine')

        food = CuisineBase(
            heading = heading_data,
            picture = picture_data,
            extract = extract_data,
            learnMore = learn_more_data,
            file = file_data,
            user=request.user
        )
        food.save()
        messages.success(request, "The cuisine created successfully!")
        return redirect('home')
    return render(request, 'addCuisine.html')

@login_required
def addCeremony(request):
    if request.method == 'POST':
        heading_data = request.POST.get('headingForCeremony')
        extract_data = request.POST.get('extractForCeremony')
        picture_data = request.FILES.get('imageForCeremony')
        learn_more_data = request.POST.get('learnMore')
        file_data = request.FILES.get('fileForCeremony')

        ceremony = CeremoniesBase(
            heading = heading_data,
            picture = picture_data,
            extract = extract_data,
            learnMore = learn_more_data,
            file = file_data,
            user=request.user
        )
        ceremony.save()
        messages.success(request, "The ceremony created successfully!")
        return redirect('home')
    return render(request, 'addCeremony.html')

@login_required
def addAttire(request):
    if request.method == 'POST':
        heading_data = request.POST.get('headingForAttire')
        extract_data = request.POST.get('extractForAttire')
        picture_data = request.FILES.get('imageForAttire')
        learn_more_data = request.POST.get('learnMore')
        file_data = request.FILES.get('fileForAttire')

        attire = AttireBase(
            heading = heading_data,
            picture = picture_data,
            extract = extract_data,
            learnMore = learn_more_data,
            file = file_data,
            user=request.user
        )
        attire.save()
        messages.success(request, "The Attire created successfully!")
        return redirect('home')
    return render(request, 'addAttire.html')

@login_required
def addQuestion(request):
    if request.method == "POST":
        question = request.POST.get("question")
        answer = request.POST.get("answer")

        QuizBase.objects.create(
            question = question,
            answer = answer,
            user=request.user
        )

    return render(request, 'addQuestions.html')


def viewHistory(request, history_id):
    history = get_object_or_404(HistoryBase, pk=history_id)

    fileIsPDF = False
    fileOutPut = None
    if history.file:
        if history.file.name.lower().endswith('.pdf'):
            fileIsPDF = True

        elif history.file.name.lower().endswith('.txt'):
            fileOutPut = history.file.read().decode('utf-8')

    elif history.extract:
        fileOutPut = history.extract



    return render(request, 'viewHistory.html', {'history': history, 'output': fileOutPut, 'fileIsPDF': fileIsPDF})


def loginR(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')
            else:

                return render(request, 'login.html', {"messages":"Invalid username or password."})
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('loginR')
    else:
        form = UserRegisterForm()

    return render(request, 'signup.html', {'form': form})

@login_required
def logoutR(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
def profile(request):
    context = {}

    if request.user.is_authenticated:
        user_entries = Entry.objects.filter(user=request.user)
        user_ceremonies = CeremoniesBase.objects.filter(user=request.user)
        user_attires = AttireBase.objects.filter(user=request.user)
        user_cuisines = CuisineBase.objects.filter(user=request.user)
        user_histories = HistoryBase.objects.filter(user=request.user)
        user_questions = QuizBase.objects.filter(user=request.user)
        user_scores = QuizScores.objects.filter(user=request.user)
        favorites = request.user.favorite_entries.all()

        context = {
            'user_entries': user_entries,
            'user_ceremonies': user_ceremonies,
            'user_attires': user_attires,
            'user_cuisines': user_cuisines,
            'user_histories':user_histories,
            'user_questions': user_questions,
            'user_scores': user_scores,
            'favorites': favorites

        }

    return render(request, 'profile.html', context)

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def admin_approval_view(request):
    pending_entries = Entry.objects.filter(status='Pending')

    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        action = request.POST.get('action')
        entry = get_object_or_404(Entry, id=entry_id)

        if action == 'approve':
            entry.status = 'Approved'
            entry.save()
        elif action == 'disapprove':
            entry.status = 'Disapproved'
            entry.save()
        elif action == 'delete':
            entry.delete()

        return redirect('admin_approval')

    context = {'pending_entries': pending_entries}
    return render(request, 'adminApproval.html', context)

@user_passes_test(is_admin)
def approveCeremony(request):
    pending_ceremonies = CeremoniesBase.objects.filter(status='Pending')

    if request.method == 'POST':
        ceremony_id = request.POST.get('ceremony_id')
        action = request.POST.get('action')
        ceremony = get_object_or_404(CeremoniesBase, id=ceremony_id)

        if action == 'approve':
            ceremony.status = 'Approved'
            ceremony.save()
        elif action == 'disapprove':
            ceremony.status = 'Disapproved'
            ceremony.save()
        elif action == 'delete':
            ceremony.delete()

        return redirect('approveCeremony')

    context = {'pending_ceremonies': pending_ceremonies}
    return render(request, 'approveCeremony.html', context)

@user_passes_test(is_admin)
def approveCuisine(request):
    pending_cuisines = CuisineBase.objects.filter(status='Pending')

    if request.method == 'POST':
        cuisine_id = request.POST.get('cuisine_id')
        action = request.POST.get('action')
        cuisine = get_object_or_404(CuisineBase, id=cuisine_id)

        if action == 'approve':
            cuisine.status = 'Approved'
            cuisine.save()
        elif action == 'disapprove':
            cuisine.status = 'Disapproved'
            cuisine.save()
        elif action == 'delete':
            cuisine.delete()

        return redirect('approveCuisine')

    context = {'pending_cuisines': pending_cuisines}
    return render(request, 'approveCuisine.html', context)

@user_passes_test(is_admin)
def approveAttire(request):
    pending_attires = AttireBase.objects.filter(status='Pending')

    if request.method == 'POST':
        attire_id = request.POST.get('attire_id')
        action = request.POST.get('action')
        attire = get_object_or_404(AttireBase, id=attire_id)

        if action == 'approve':
            attire.status = 'Approved'
            attire.save()
        elif action == 'disapprove':
            attire.status = 'Disapproved'
            attire.save()
        elif action == 'delete':
            attire.delete()

        return redirect('approveAttire')

    context = {'pending_attires': pending_attires}
    return render(request, 'approveAttire.html', context)

@user_passes_test(is_admin)
def approveHistory(request):
    pending_histories = HistoryBase.objects.filter(status='Pending')

    if request.method == 'POST':
        history_id = request.POST.get('history_id')
        action = request.POST.get('action')
        history = get_object_or_404(HistoryBase, id=history_id)

        if action == 'approve':
            history.status = 'Approved'
            history.save()
        elif action == 'disapprove':
            history.status = 'Disapproved'
            history.save()
        elif action == 'delete':
            history.delete()

        return redirect('approveHistory')

    context = {'pending_histories': pending_histories}
    return render(request, 'approveHistory.html', context)

@user_passes_test(is_admin)
def approveQuestion(request):
    pending_questions = QuizBase.objects.filter(status='Pending')

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        action = request.POST.get('action')
        question = get_object_or_404(QuizBase, id=question_id)

        if action == 'approve':
            question.status = 'Approved'
            question.save()
        elif action == 'disapprove':
            question.status = 'Disapproved'
            question.save()
        elif action == 'delete':
            question.delete()

        return redirect('approveQuestion')

    context = {'pending_questions': pending_questions}
    return render(request, 'approveQuestion.html', context)

@login_required
def deleteEntry(request, entry_id):
    if request.method == 'POST' and request.user.is_authenticated:
        entry = get_object_or_404(Entry, pk=entry_id, user=request.user)
        entry.delete()
    return redirect('profile')

@login_required
def deleteQuestion(request, question_id):
    if request.method == 'POST' and request.user.is_authenticated:
        question = get_object_or_404(QuizBase, pk=question_id, user=request.user)
        question.delete()
    return redirect('profile')

@login_required
def deleteCeremony(request, entry_id):
    if request.method == 'POST' and request.user.is_authenticated:
        ceremony = get_object_or_404(CeremoniesBase, pk=entry_id, user=request.user)
        ceremony.delete()
    return redirect('profile')

@login_required
def deleteAttire(request, entry_id):
    if request.method == 'POST' and request.user.is_authenticated:
        attire = get_object_or_404(AttireBase, pk=entry_id, user=request.user)
        attire.delete()
    return redirect('profile')

@login_required
def deleteHistory(request, entry_id):
    if request.method == 'POST' and request.user.is_authenticated:
        history = get_object_or_404(HistoryBase, pk=entry_id, user=request.user)
        history.delete()
    return redirect('profile')

@login_required
def deleteCuisine(request, entry_id):
    if request.method == 'POST' and request.user.is_authenticated:
        cuisine = get_object_or_404(CuisineBase, pk=entry_id, user=request.user)
        cuisine.delete()
    return redirect('profile')

@login_required
def editEntry(request, entry_id):
    if not request.user.is_authenticated:
        return redirect('login')

    entry = get_object_or_404(Entry, pk=entry_id, user=request.user)

    if request.method == 'POST':
        try:

            entry.isizulu = request.POST.get('zulu-phrase')
            entry.english = request.POST.get('english-translation')
            entry.isixhosa = request.POST.get('isixhosa-translation')
            entry.isipedi = request.POST.get('isipedi-translation')
            entry.extract = request.POST.get('extract')
            entry.word_usage = request.POST.get('word-usage')
            entry.learn_more = request.POST.get('learnMore')
            entry.save()

            messages.success(request, "Entry successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update entry: {e}")


    context = {'entry': entry}
    return render(request, 'editEntry.html', context)

@login_required
def editQuestion(request, question_id):
    if not request.user.is_authenticated:
        return redirect('login')

    question = get_object_or_404(QuizBase, pk=question_id, user=request.user)

    if request.method == 'POST':
        try:

            question.question = request.POST.get('question')
            question.answer = request.POST.get('answer')
            question.save()

            messages.success(request, "Quiz question successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update quiz question: {e}")


    context = {'question': question}
    return render(request, 'editQuestion.html', context)

@login_required
def editCeremony(request, ceremony_id):
    if not request.user.is_authenticated:
        return redirect('login')

    ceremony = get_object_or_404(CeremoniesBase, pk=ceremony_id, user=request.user)

    if request.method == 'POST':
        try:
            heading_data = request.POST.get('headingForCeremony')
            extract_data = request.POST.get('extractForCeremony')
            picture_data = request.FILES.get('imageForCeremony')
            learn_more_data = request.POST.get('learnMore')
            file_data = request.FILES.get('fileForCeremony')

            ceremony.heading = heading_data
            ceremony.picture = picture_data
            ceremony.extract = extract_data
            ceremony.learnMore = learn_more_data
            ceremony.file = file_data

            ceremony.save()

            messages.success(request, "Ceremony successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update ceremony: {e}")


    context = {'ceremony': ceremony}
    return render(request, 'editCeremony.html', context)

@login_required
def editCuisine(request, cuisine_id):
    if not request.user.is_authenticated:
        return redirect('login')

    cuisine = get_object_or_404(CuisineBase, pk=cuisine_id, user=request.user)

    if request.method == 'POST':
        try:

            heading_data = request.POST.get('headingForCuisine')
            extract_data = request.POST.get('extractForCuisine')
            picture_data = request.FILES.get('imageForCuisine')
            learn_more_data = request.POST.get('learnMore')
            file_data = request.FILES.get('fileForCuisine')

            cuisine.heading = heading_data
            cuisine.picture = picture_data
            cuisine.learnMore = learn_more_data
            cuisine.file = file_data
            cuisine.extract = extract_data

            cuisine.save()

            messages.success(request, "Cuisine successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update cuisine: {e}")


    context = {'cuisine': cuisine}
    return render(request, 'editCuisine.html', context)

@login_required
def editAttire(request, attire_id):
    if not request.user.is_authenticated:
        return redirect('login')

    attire = get_object_or_404(AttireBase, pk=attire_id, user=request.user)

    if request.method == 'POST':
        try:

            heading_data = request.POST.get('headingForAttire')
            extract_data = request.POST.get('extractForAttire')
            picture_data = request.FILES.get('imageForAttire')
            learn_more_data = request.POST.get('learnMore')
            file_data = request.FILES.get('fileForAttire')

            attire.heading = heading_data
            attire.picture = picture_data
            attire.learnMore = learn_more_data
            attire.file = file_data
            attire.extract = extract_data

            attire.save()

            messages.success(request, "Attire successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update attire: {e}")


    context = {'attire': attire}
    return render(request, 'editAttire.html', context)

@login_required
def editHistory(request, history_id):
    if not request.user.is_authenticated:
        return redirect('login')

    history = get_object_or_404(Entry, pk=history_id, user=request.user)

    if request.method == 'POST':
        try:

            heading_data = request.POST.get('headingForHistory')
            extract_data = request.POST.get('extractForHistory')
            picture_file = request.FILES.get('ImageForHistory')
            file_data = request.FILES.get('fileForHistory')

            history.heading = heading_data
            history.picture = picture_file
            history.file = file_data
            history.extract = extract_data

            history.save()

            messages.success(request, "History successfully updated!")
            return redirect('profile')

        except Exception as e:
            messages.error(request, f"Failed to update history: {e}")


    context = {'history': history}
    return render(request, 'editHistory.html', context)

def stats(request):
    approved_counts = {}

    total_words_result = WordFrequency.objects.aggregate(total=Sum('count'))
    total_words = total_words_result.get('total') or 0
    unique_words = WordFrequency.objects.count()
    average_length_result = WordFrequency.objects.aggregate(
        avg_length=Avg(Length('word'))
    )
    average_word_length = average_length_result.get('avg_length') or 0.0

    if request.user.is_authenticated:
        user = request.user
        approved_counts['Entries'] = Entry.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['Ceremonies'] = CeremoniesBase.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['Attire'] = AttireBase.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['Cuisine'] = CuisineBase.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['History'] = HistoryBase.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['Quizzes'] = QuizBase.objects.filter(
            user=user,
            status='Approved'
        ).count()

        approved_counts['Total'] = sum(approved_counts.values())


    entries = Entry.objects.all().order_by('-word_frequency')
    leaderboard_data = QuizScores.objects.values('user__username', 'user__id').annotate(
        quiz_takes=Count('user'),
        average_score=Avg('score')
    ).order_by('-average_score')

    user_stats = None
    if request.user.is_authenticated:
        user_stats = QuizScores.objects.filter(user=request.user).aggregate(
            user_quiz_takes=Count('user'),
            user_average_score=Avg('score')
        )
        user_stats['username'] = request.user.username

        ranked_list = list(leaderboard_data)
        user_rank = next((i + 1 for i, entry in enumerate(ranked_list)
                          if entry['user__id'] == request.user.id), None)
        user_stats['rank'] = user_rank


    context = {
        'approved_counts': approved_counts,
        'leaderboard': leaderboard_data,
        'user_stats': user_stats,
         "entries": entries,
        'total_words': total_words,
        'unique_words': unique_words,
        'average_word_length': f"{average_word_length:.2f}" if average_word_length else "0.00",

        }
    return render(request, 'stats.html', context)

def quiz(request):
    return render(request, 'quiz.html')
def search_word(request):
    return render(request, "corpusapp/search.html")

@login_required
def like_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    if entry.likes.filter(id=request.user.id).exists():
        entry.likes.remove(request.user)
    else:
        entry.likes.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', '/'))

def leaderboard(request):
    leaderboard_data = QuizScores.objects.values('user__username', 'user__id').annotate(
        quiz_takes=Count('user'),
        average_score=Avg('score')
    ).order_by('-average_score')

    context = {
        'leaderboard': leaderboard_data
    }
    return render(request, 'leaderboard.html', context)

client = genai.Client(api_key="AIzaSyClIrPChFa-GaJSud2-PkGVnmHvG23-Mc8")
@csrf_exempt
def translate_text(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        text_to_translate = data.get('text')
        target_lang = data.get('target_lang')

        if not text_to_translate or not target_lang:
            return JsonResponse({'error': 'Missing text or target language'}, status=400)

        prompt = f"Translate this text into {target_lang}. Return only the translation: '{text_to_translate}'"

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        translated_text = response.text.strip()

        return JsonResponse({'translation': translated_text})

    except APIError:
        return JsonResponse({'error': 'Translation service failed.'}, status=500)
    except Exception:
        return JsonResponse({'error': 'An internal error occurred.'}, status=500)