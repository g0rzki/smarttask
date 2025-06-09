from app import db
from .models import User, Task
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

def seed_db():
    if User.query.count() > 0:
        print("Baza nie jest pusta. Seeder nie wykonał się.")
        return

    # Dodaj 10 użytkowników z łatwymi hasłami
    users = []
    for i in range(1, 11):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=generate_password_hash(f"user{i}")
        )
        db.session.add(user)
        users.append(user)
    db.session.commit()

    # Priorytety i kategorie przykładowe
    priorities = ["Low", "Medium", "High"]
    categories = ["Dom", "Praca", "Studia", "Sport", "Zdrowie", "Hobby"]

    # Dodaj przykładowe zadania dla każdego użytkownika
    for user in users:
        tasks = []
        for j in range(10):
            priority = random.choice(priorities)
            category = random.choice(categories)
            # Data: część zadań w przyszłości, część w przeszłości
            days_offset = random.randint(-5, 15)
            task = Task(
                title=f"Zadanie {j+1}",
                due_date=date.today() + timedelta(days=days_offset),
                priority=priority,
                category=category,
                user_id=user.id
            )
            tasks.append(task)
        db.session.add_all(tasks)
    db.session.commit()
    print("Baza została zasilona przykładowymi użytkownikami i zadaniami.")