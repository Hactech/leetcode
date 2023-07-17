from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser


class Questions(models.Model):
    heading = models.CharField(max_length=50, unique=True)
    discription = models.CharField(max_length=500)
    constraint = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=20, default="easy")


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        user = self.model(username=username,
                          password=password,
                          **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username=username, password=password, **extra_fields)


class User(AbstractUser):
    # id = models.IntegerField(db_column="_id", primary_key=True)
    username = models.CharField(max_length=20, unique=True)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.CharField(max_length=30)
    password = models.CharField(max_length=20)
    score = models.IntegerField(default=0)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["password"]

    def __str__(self):
        return self.username


class Submission(models.Model):
    result = models.CharField(max_length=50, default="FAILED")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    problem = models.ForeignKey(Questions, null=True, on_delete=models.SET_NULL)
    langauge = models.CharField(max_length=50, default="C++")
    submission_time = models.DateTimeField(auto_now_add=True, null=True)


class TestCases(models.Model):
    problem = models.ForeignKey(Questions, on_delete=models.CASCADE)
    input = models.TextField()
    output = models.TextField()

    def __str__(self):
        return "TC: " + str(self.id) + " for problem :" + str(self.problem)
