from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Task
from . import db, login_manager
from datetime import datetime, date, timedelta

main = Blueprint('main', __name__)

# Funkcja do wczytywania zalogowanego użytkownika
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Przekierowanie ze strony głównej do logowania
@main.route('/')
def home():
    return redirect(url_for('main.login'))

# Rejestracja nowego użytkownika
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Użytkownik już istnieje')
            return redirect(url_for('main.register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Zarejestrowano pomyślnie')
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Logowanie użytkownika
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Nieprawidłowe dane logowania')
    return render_template('login.html')

# Wylogowanie użytkownika
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# Panel główny użytkownika z filtrowaniem zadań
@main.route('/dashboard')
@login_required
def dashboard():
    filter_status = request.args.get('status', 'pending')
    filter_due = request.args.get('due')
    filter_priority = request.args.get('priority')
    filter_category = request.args.get('category')
    sort = request.args.get('sort', 'due')  
    today = date.today()

    tasks = Task.query.filter_by(user_id=current_user.id)

    if filter_status == 'done':
        tasks = tasks.filter_by(is_completed=True)
    elif filter_status == 'pending':
        tasks = tasks.filter_by(is_completed=False)

    if filter_due:
        now = datetime.now().date()
        if filter_due == 'today':
            tasks = tasks.filter(db.func.date(Task.due_date) == now)
        elif filter_due == 'tomorrow':
            tasks = tasks.filter(db.func.date(Task.due_date) == now + timedelta(days=1))
        elif filter_due == '3days':
            end_date = now + timedelta(days=3)
            tasks = tasks.filter(db.func.date(Task.due_date) <= end_date)
        elif filter_due == '7days':
            end_date = now + timedelta(days=7)
            tasks = tasks.filter(db.func.date(Task.due_date) <= end_date)
        elif filter_due == 'late':
            tasks = tasks.filter(db.func.date(Task.due_date) < now)
        

    if filter_priority:
        tasks = tasks.filter_by(priority=filter_priority)

    if filter_category:
        tasks = tasks.filter(Task.category.ilike(f'%{filter_category}%'))

    if sort == 'priority':
        priority_order = db.case(
            (Task.priority == 'High', 1),
            (Task.priority == 'Medium', 2),
            (Task.priority == 'Low', 3),
            else_=4
        )
        tasks = tasks.order_by(priority_order, Task.due_date)
    else:
        tasks = tasks.order_by(Task.due_date)

    tasks = tasks.all()

    # Dni do końca zadania i kolor
    for task in tasks:
        if task.is_completed:
            task.days_left_text = "Wykonano"
            task.days_left_color = "text-grey-500"
        elif task.due_date:
            due_date = task.due_date.date() if hasattr(task.due_date, 'date') else task.due_date
            days_left = (due_date - today).days
            task.days_left = abs(days_left)

            if days_left == 1 or days_left == -1:
                day_word = "dzień"
            else:
                day_word = "dni"

            if days_left < 0:
                task.days_left_text = f"{day_word} po terminie"
                task.days_left_color = "text-red-900"
            else:
                task.days_left_text = f"{day_word} do końca"
                if days_left <= 3:
                    task.days_left_color = "text-red-500"
                elif 4 <= days_left <= 7:
                    task.days_left_color = "text-yellow-500"
                else:
                    task.days_left_color = "text-green-500"
        else:
            task.days_left = None
            task.days_left_text = ""
            task.days_left_color = "text-gray-500"

    unique_categories = db.session.query(Task.category).filter(Task.user_id == current_user.id).distinct().all()
    unique_categories = [c[0] for c in unique_categories if c[0]]

    return render_template('dashboard.html', tasks=tasks, today=today, unique_categories=unique_categories)

# Tworzenie nowego zadania
@main.route('/task/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        priority = request.form['priority']
        category = request.form['category']

        task = Task(title=title, due_date=datetime.strptime(due_date, '%Y-%m-%d').date(), priority=priority, category=category, owner=current_user)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('task_form.html', task=None)

# Edycja istniejącego zadania
@main.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        task.title = request.form['title']
        task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        task.priority = request.form['priority']
        task.category = request.form['category']
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('task_form.html', task=task)

# Usuwanie zadania
@main.route('/task/<int:task_id>/delete')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner == current_user:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('main.dashboard'))

# Zmiana statusu ukończenia zadania
@main.route('/task/<int:task_id>/toggle')
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner == current_user:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for('main.dashboard'))

# Statystyki użytkownika
@main.route('/statistics')
@login_required
def statistics():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.is_completed)
    pending_tasks = sum(1 for t in tasks if not t.is_completed)
    overdue_tasks = sum(
        1 for t in tasks
        if t.due_date and not t.is_completed and (
            (t.due_date.date() if hasattr(t.due_date, 'date') else t.due_date) < date.today()
        )
    )
    low_priority = sum(1 for t in tasks if not t.is_completed and t.priority == 'Low')
    medium_priority = sum(1 for t in tasks if not t.is_completed and t.priority == 'Medium')
    high_priority = sum(1 for t in tasks if not t.is_completed and t.priority == 'High')

    return render_template(
        'statistics.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        low_priority=low_priority,
        medium_priority=medium_priority,
        high_priority=high_priority
    )
