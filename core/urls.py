from django.urls import path
from . import views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),

    path('register/', views.register_view, name='register'),

    path('login/', views.login_view, name='login'),

    path('logout/', views.logout_view, name='logout'),

    # PROJECT URLS
    path('create-project/', views.create_project, name='create_project'),

    path('edit-project/<int:project_id>/', views.edit_project, name='edit_project'),

    path('delete-project/<int:project_id>/', views.delete_project, name='delete_project'),

    # TASK URLS
    path('project/<int:project_id>/tasks/', views.project_tasks, name='project_tasks'),

    path('project/<int:project_id>/create-task/', views.create_task, name='create_task'),

    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),

    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),


    path(
    'task/<int:task_id>/update-status/',
    views.update_task_status,
    name='update_task_status'
),

path(
    'project/<int:project_id>/create-task/',
    views.create_task,
    name='create_task'
),
path(
    'notification/<int:notification_id>/read/',
    views.mark_notification_read,
    name='mark_notification_read'
),
path(
    'project/<int:project_id>/members/',
    views.manage_members,
    name='manage_members'
),
path('reminders/', views.task_reminders, name='task_reminders'),
path('profile/', views.profile, name='profile'),
path(
    'change-password/',
    views.change_password,
    name='change_password'
),

path('calendar/', views.task_calendar, name='task_calendar'),
]