from tempfile import template

from django.urls import path
from . import views
from .views import (PostListView,
 PostDetailView,
 PostCreateView,
 PostUpdateView,
 PostDeleteView,
 UserPostListView)

urlpatterns = [
    path('', PostListView.as_view(), name='blog-home'),
    path('user/<str:username>/', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete', PostDeleteView.as_view(), name='post-delete'),
    path('about/', views.about, name='blog-about'),
    path('game/game_begin', views.game_begin, name='game-begin'),
    path('game/challenge/<int:run_id>/continue/', views.challenge_continue, name='challenge-continue'),
    path('game/production', views.game, name='game-production'),
    path('demand/', views.demand_distribution_view, name='demand_distribution'),
    path('insurance/', views.insurance_distribution_view, name='insurance_distribution'),
    path('turn_summary/', views.turn_summary, name='turn-summary'),
    path('financial_history/<str:player>/', views.financial_history, name='financial-history'),
    path('financial_summary_card/<int:pk>/', views.financial_summary_card, name='financial-summary-card'),
    path('interest-rate-distribution/', views.interest_rate_distribution_view, name='interest_rate_distribution'),
    path('new_product_success_distribution/', views.rnd_new_product_success_distribution_view, name='new-product-success-distribution'),
    path('gross_profit_analysis/', views.gross_profit_analysis, name='gross-profit-analysis'),
    path('game/history/', views.game_history, name='game-history'),
]
