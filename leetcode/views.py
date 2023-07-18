import os

import docker
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from time import time
from django.conf import settings

from leetcode.models import Questions, TestCases, Submission
from leetcode.models import User
import subprocess


def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        user = authenticate(username=username, password=pass1)
        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, "leetcode/home.html", {"fname": fname})
        else:
            messages.error(request, "Bad Credentials")
    return render(request, "leetcode/signin.html")


def signout(request):
    return render(request, "leetcode/signin.html")


def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        User.objects.create_user(username=username, password=pass1, firstname=fname, lastname=lname
                                 , email=email)

        return redirect('signin')

    return render(request, "leetcode/signup.html")


@login_required(login_url='signin')
def home(request):
    mydata = Questions.objects.all().values()
    paginator = Paginator(mydata, 4)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(1)
    template = loader.get_template("leetcode/home.html")
    context = {
        'questions': data,
    }
    return HttpResponse(template.render(context, request))


@login_required(login_url='signin')
def leaderBoard(request):
    mydata = User.objects.order_by('-score')[:10]
    paginator = Paginator(mydata, 10)
    page = request.GET.get('page')
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(1)
    template = loader.get_template("leetcode/leaderBoard.html")
    context = {
        'users': data,
    }
    return HttpResponse(template.render(context, request))


@login_required(login_url='signin')
def detail(request, question_id):
    mydata = Questions.objects.get(id=question_id)
    print(mydata.heading)
    return render(request, "leetcode/P1.html", {'question': mydata})


@login_required(login_url='signin')
def submission(request):
    submissions = Submission.objects.filter(user_id=request.user.id).order_by('-submission_time')
    paginator = Paginator(submissions, 6)
    page = request.GET.get('page')
    print(page)
    try:
        data = paginator.get_page(page)
    except PageNotAnInteger:
        data = paginator.get_page(1)
    except EmptyPage:
        data = paginator.get_page(1)
    print(submissions)
    return render(request, 'leetcode/submission.html', {'submissions': data})


# Shows the verdict to the submission
@login_required(login_url='login')
def verdictPage(request, user_id, question_id):
    if request.method == 'POST':
        # setting docker-client
        docker_client = docker.from_env()
        Running = "running"

        problem = Questions.objects.get(id=question_id)
        testcase = TestCases.objects.get(problem_id=question_id)
        # replacing \r\n by \n in original output to compare it with the usercode output
        testcase.output = testcase.output.replace('\r\n', '\n').strip()

        # score of a problem
        if problem.difficulty == "easy":
            score = 10
        elif problem.difficulty == "medium":
            score = 30
        else:
            score = 50

        # setting verdict to wrong by default
        verdict = "Wrong Answer"
        res = ""
        run_time = 0

        # extract data from form
        user_code = ''
        user_code = request.POST['user_code']
        user_code = user_code.replace('\r\n', '\n').strip()

        language = request.POST['language']
        submission = Submission(user=request.user, problem=problem)
        submission.save()

        filename = str(submission.id)

        # if user code is in C++
        extension = ".cpp"
        cont_name = "oj-cpp"
        compile = f"g++ -o {filename} {filename}.cpp"
        clean = f"{filename} {filename}.cpp"
        docker_img = "gcc:11.2.0"
        exe = f"./{filename}"

        file = filename + extension
        filepath = settings.FILES_DIR + "/" + file
        code = open(filepath, "w")
        code.write(user_code)
        code.close()

        # checking if the docker container is running or not
        try:
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            container_is_running = (container_state['Status'] == Running)
            if not container_is_running:
                subprocess.run(f"docker start {cont_name}", shell=True)
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}", shell=True)

        # copy/paste the .cpp file in docker container
        subprocess.run(f"docker cp {filepath} {cont_name}:/{file}", shell=True)

        # compiling the code
        cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} rm {file}", shell=True)

        else:
            # running the code on given input and taking the output in a variable in bytes
            start = time()
            try:
                res = subprocess.run(f"docker exec {cont_name} sh -c 'echo \"{testcase.input}\" | {exe}'",
                                     capture_output=True, timeout=2, shell=True)
                run_time = time() - start
                subprocess.run(f"docker exec {cont_name} rm {clean}", shell=True)
            except subprocess.TimeoutExpired:
                run_time = time() - start
                verdict = "Time Limit Exceeded"
                subprocess.run(f"docker container kill {cont_name}", shell=True)
                subprocess.run(f"docker start {cont_name}", shell=True)
                subprocess.run(f"docker exec {cont_name} rm {clean}", shell=True)

            if verdict != "Time Limit Exceeded" and res.returncode != 0:
                verdict = "Runtime Error"

        user_stderr = ""
        user_stdout = ""
        if verdict == "Compilation Error":
            user_stderr = cmp.stderr.decode('utf-8')
            score = 0

        elif verdict == "Wrong Answer":
            user_stdout = res.stdout.decode('utf-8')
            if str(user_stdout) == str(testcase.output):
                verdict = "Accepted"
            testcase.output += '\n'  # added extra line to compare user output having extra ling at the end of their output
            if str(user_stdout) == str(testcase.output):
                verdict = "Accepted"

        # creating Solution class objects and showing it on leaderboard
        # user = User.objects.get(username=request.user)
        # previous_verdict = Submission.objects.filter(user=user.id, problem=problem, verdict="Accepted")
        # if len(previous_verdict) == 0 and verdict == "Accepted":
        #     user.total_score += score
        #     user.total_solve_count += 1
        #     if problem.difficulty == "Easy":
        #         user.easy_solve_count += 1
        #     elif problem.difficulty == "Medium":
        #         user.medium_solve_count += 1
        #     else:
        #         user.tough_solve_count += 1
        #     user.save()
        user = User.objects.get(id=user_id)
        user.score = user.score + score
        user.save()
        submission.result = verdict
        submission.save()
        os.remove(filepath)
        context = {'verdict': verdict}
        return render(request, 'leetcode/verdict.html', context)
