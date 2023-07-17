from django.urls import path

from . import views

urlpatterns = [
    path("signin", views.signin, name="signin"),
    path('', views.home, name="home"),
    path("signup", views.signup, name="signup"),
    path("signout", views.signout, name="signout"),
    path("problem/<int:question_id>/", views.detail, name="detail"),
    path("problem/<int:question_id>/submission/<int:user_id>/", views.verdictPage, name="verdict"),
    path("leaders", views.leaderBoard, name="leaderBoard"),
    path("user/submission", views.submission, name="submission"),
]
