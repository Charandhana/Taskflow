
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth import update_session_auth_hash
from .models import Project, Task, Comment, Activity, Notification


# -------------------------------
# ACTIVITY AND NOTIFICATION
# -------------------------------

def add_activity(user, project, message):
    Activity.objects.create(
        user=user,
        project=project,
        message=message
    )


def create_notification(user, message):
    Notification.objects.create(
        recipient=user,
        message=message
    )


# -------------------------------
# REGISTER
# -------------------------------

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username or not password:
            messages.error(request, 'All fields are required.')

        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')

        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')

        else:
            user = User.objects.create_user(
                username=username,
                password=password
            )
            login(request, user)
            return redirect('dashboard')

    return render(request, 'core/register.html')


# -------------------------------
# LOGIN
# -------------------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'core/login.html')


# -------------------------------
# LOGOUT
# -------------------------------

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)

    return redirect('login')


# -------------------------------
# DASHBOARD
# -------------------------------

@login_required
def dashboard(request):
    projects = Project.objects.filter(
        members=request.user
    ).distinct()
    search = request.GET.get('search', '').strip()

    if search:
        projects = projects.filter(name__icontains=search)

    category = request.GET.get('category', '')

    if category:
        projects = projects.filter(category=category)

    total_projects = projects.count()

    all_tasks = Task.objects.filter(project__in=projects)

    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status='Completed').count()
    pending_tasks = total_tasks - completed_tasks

    progress = (
        int((completed_tasks / total_tasks) * 100)
        if total_tasks > 0 else 0
    )

    project_data = []

    for project in projects:
        tasks = project.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status='Completed').count()

        percentage = (
            int((completed / total) * 100)
            if total > 0 else 0
        )

        project_data.append({
            'project': project,
            'total': total,
            'completed': completed,
            'percentage': percentage
        })

    activities = Activity.objects.filter(
        project__in=projects
    ).select_related(
        'user', 'project'
    ).order_by('-created_at')[:10]

    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    return render(request, 'core/dashboard.html', {
        'projects': projects,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'progress': progress,
        'project_data': project_data,
        'activities': activities,
        'notifications': notifications,
        'search': search,
        'category': category,
        'categories': Project.CATEGORY_CHOICES,
    })


# -------------------------------
# CREATE PROJECT
# -------------------------------

@login_required
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'Others')

        if not name:
            messages.error(request, 'Project name is required.')
        else:
            project = Project.objects.create(
                name=name,
                description=description,
                created_by=request.user,
                category=category
            )

            project.members.add(request.user)

            add_activity(
                request.user,
                project,
                'created the project'
            )

            messages.success(request, 'Project created successfully!')
            return redirect('dashboard')

    return render(request, 'core/create_project.html')


# -------------------------------
# EDIT PROJECT
# -------------------------------

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        created_by=request.user
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            project.name = name
            project.description = description
            project.save()

            messages.success(request, 'Project updated successfully!')
            return redirect('dashboard')

        messages.error(request, 'Project name is required.')

    return render(request, 'core/edit_project.html', {
        'project': project
    })


# -------------------------------
# DELETE PROJECT
# -------------------------------

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        created_by=request.user
    )

    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')

    return redirect('dashboard')


# -------------------------------
# VIEW PROJECT TASKS
# -------------------------------

@login_required
def project_tasks(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        members=request.user
    )

    tasks = Task.objects.filter(
        project=project
    ).select_related('assigned_to')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    assigned_to = request.GET.get('assigned_to', '')

    if search:
        tasks = tasks.filter(title__icontains=search)

    if status in ['To Do', 'In Progress', 'Completed']:
        tasks = tasks.filter(status=status)

    if assigned_to.isdigit():
        tasks = tasks.filter(assigned_to_id=int(assigned_to))

    todo_tasks = tasks.filter(status='To Do')
    progress_tasks = tasks.filter(status='In Progress')
    completed_tasks = tasks.filter(status='Completed')

    return render(request, 'core/tasks.html', {
        'project': project,
        'tasks': tasks,
        'todo_tasks': todo_tasks,
        'progress_tasks': progress_tasks,
        'completed_tasks': completed_tasks,
        'today': timezone.localdate(),
        'members': project.members.all(),
        'search': search,
        'selected_status': status,
        'selected_member': assigned_to,
    })

# -------------------------------
# CREATE TASK
# -------------------------------

@login_required
def create_task(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        members=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'Medium')
        assigned_to_id = request.POST.get('assigned_to')
        due_date_value = request.POST.get('due_date')

        if not title:
            messages.error(request, 'Task title is required.')

        else:
            assigned_to = None

            if assigned_to_id:
                assigned_to = get_object_or_404(
                    project.members,
                    id=assigned_to_id
                )

            due_date = (
                parse_date(due_date_value)
                if due_date_value else None
            )

            if due_date_value and due_date is None:
                messages.error(request, 'Enter a valid due date.')

            else:
                task = Task.objects.create(
                    project=project,
                    title=title,
                    description=description,
                    assigned_to=assigned_to,
                    due_date=due_date,
                    priority=priority,
                    attachment=request.FILES.get('attachment')
                )

                add_activity(
                    request.user,
                    project,
                    f'created a task: {title}'
                )

                if assigned_to and assigned_to != request.user:
                    create_notification(
                        assigned_to,
                        f'You have been assigned a new task: {title}'
                    )

                messages.success(request, 'Task created successfully!')
                return redirect('project_tasks', project_id=project.id)

    return render(request, 'core/create_task.html', {
        'project': project,
        'members': project.members.all()
    })


# -------------------------------
# EDIT TASK
# -------------------------------

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        project__members=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to')
        due_date_value = request.POST.get('due_date')

        if not title:
            messages.error(request, 'Task title is required.')

        else:
            assigned_to = None

            if assigned_to_id:
                assigned_to = get_object_or_404(
                    task.project.members,
                    id=assigned_to_id
                )

            due_date = (
                parse_date(due_date_value)
                if due_date_value else None
            )

            if due_date_value and due_date is None:
                messages.error(request, 'Enter a valid due date.')

            else:
                task.title = title
                task.description = description
                task.assigned_to = assigned_to
                task.due_date = due_date
                task.save()

                add_activity(
                    request.user,
                    task.project,
                    f'updated the task: {title}'
                )

                messages.success(request, 'Task updated successfully!')
                return redirect(
                    'project_tasks',
                    project_id=task.project.id
                )

    return render(request, 'core/edit_task.html', {
        'task': task,
        'project': task.project,
        'members': task.project.members.all()
    })


# -------------------------------
# DELETE TASK
# -------------------------------

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        project__members=request.user
    )

    project_id = task.project.id

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')

    return redirect('project_tasks', project_id=project_id)


# -------------------------------
# UPDATE TASK STATUS
# -------------------------------

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        project__members=request.user
    )

    if request.method == 'POST':
        status = request.POST.get('status')

        valid_statuses = [
            'To Do',
            'In Progress',
            'Completed'
        ]

        if status in valid_statuses:
            task.status = status
            task.save()

            add_activity(
                request.user,
                task.project,
                f'changed the status of {task.title} to {status}'
            )

            messages.success(request, 'Task status updated!')
        else:
            messages.error(request, 'Invalid task status.')

    return redirect(
        'project_tasks',
        project_id=task.project.id
    )


# -------------------------------
# TASK DETAILS AND COMMENTS
# -------------------------------

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        project__members=request.user
    )

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        if content:
            Comment.objects.create(
                task=task,
                user=request.user,
                content=content
            )

            add_activity(
                request.user,
                task.project,
                f'commented on {task.title}'
            )

            for member in task.project.members.exclude(
                id=request.user.id
            ):
                create_notification(
                    member,
                    f'{request.user.username} commented on {task.title}'
                )

            messages.success(request, 'Comment added successfully!')
            return redirect('task_detail', task_id=task.id)

        messages.error(request, 'Comment cannot be empty.')

    comments = task.comments.select_related(
        'user'
    ).order_by('-created_at')

    return render(request, 'core/task_detail.html', {
        'task': task,
        'comments': comments
    })


# -------------------------------
# DELETE COMMENT
# -------------------------------

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        task__project__members=request.user
    )

    task_id = comment.task.id

    if request.method == 'POST' and comment.user == request.user:
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')

    return redirect('task_detail', task_id=task_id)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    if request.method == 'POST':
        notification.is_read = True
        notification.save()

    return redirect('dashboard')

@login_required
def manage_members(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        created_by=request.user
    )

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()

        try:
            user = User.objects.get(username=username)

            if project.members.filter(id=user.id).exists():
                messages.warning(request, 'User is already a member.')
            else:
                project.members.add(user)
                messages.success(request, 'Member added successfully!')

                create_notification(
                    user,
                    f'You have been added to project: {project.name}'
                )

                add_activity(
                    request.user,
                    project,
                    f'added {username} to the project'
                )

        except User.DoesNotExist:
            messages.error(request, 'User does not exist.')

    return render(request, 'core/manage_members.html', {
        'project': project,
        'members': project.members.all()
    })

@login_required
def task_reminders(request):
    today = timezone.localdate()

    upcoming_tasks = Task.objects.filter(
        project__members=request.user,
        assigned_to=request.user,
        due_date__gte=today,
        due_date__lte=today + timezone.timedelta(days=3)
    ).order_by('due_date')

    overdue_tasks = Task.objects.filter(
        project__members=request.user,
        assigned_to=request.user,
        due_date__lt=today
    ).exclude(status='Completed').order_by('due_date')

    return render(request, 'core/reminders.html', {
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'today': today,
    })

@login_required
def profile(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        request.user.email = email
        request.user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'core/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')

        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')

        elif len(new_password) < 8:
            messages.error(request, 'Password must contain at least 8 characters.')

        else:
            request.user.set_password(new_password)
            request.user.save()

            update_session_auth_hash(request, request.user)

            messages.success(request, 'Password changed successfully!')
            return redirect('profile')

    return render(request, 'core/change_password.html')

@login_required
def task_calendar(request):
    tasks = Task.objects.filter(
        project__members=request.user,
        due_date__isnull=False
    )

    events = []

    for task in tasks:
        events.append({
            'title': task.title,
            'start': task.due_date.isoformat(),
            'url': f'/task/{task.id}/comments/'
        })

    return render(request, 'core/calendar.html', {
        'events': events
    })