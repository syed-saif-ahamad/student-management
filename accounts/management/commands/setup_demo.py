import os
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from attendance.models import Attendance
from marks.models import Marks
from students.models import Student


class Command(BaseCommand):
    help = 'Create role groups, demo faculty/students, and sample data'

    def handle(self, *args, **options):
        faculty_group, _ = Group.objects.get_or_create(name=settings.FACULTY_GROUP)
        student_group, _ = Group.objects.get_or_create(name=settings.STUDENT_GROUP)

        faculty, created = User.objects.get_or_create(
            username='faculty',
            defaults={'email': 'faculty@sms.edu', 'first_name': 'Demo', 'last_name': 'Faculty'},
        )
        if created:
            faculty.set_password('faculty123')
            faculty.save()
        faculty.groups.add(faculty_group)

        demo_students = [
            ('CS001', 'Alice Johnson', 'alice@sms.edu', 'Computer Science', 2, '9876543210'),
            ('CS002', 'Bob Smith', 'bob@sms.edu', 'Computer Science', 2, '9876543211'),
            ('CS003', 'Carol Williams', 'carol@sms.edu', 'Computer Science', 3, '9876543212'),
            ('EE001', 'David Brown', 'david@sms.edu', 'Electrical Engineering', 2, '9876543213'),
            ('ME001', 'Eva Davis', 'eva@sms.edu', 'Mechanical Engineering', 1, '9876543214'),
        ]

        joining = date.today() - timedelta(days=365)
        created_students = []

        for roll, name, email, dept, year, phone in demo_students:
            user, u_created = User.objects.get_or_create(
                username=roll.lower(),
                defaults={'email': email, 'first_name': name.split()[0]},
            )
            if u_created:
                user.set_password('student123')
                user.save()
            user.groups.add(student_group)

            student, _ = Student.objects.get_or_create(
                roll_no=roll,
                defaults={
                    'user': user,
                    'name': name,
                    'email': email,
                    'department': dept,
                    'year': year,
                    'phone': phone,
                    'joining_date': joining,
                },
            )
            created_students.append(student)

        subjects = ['Mathematics', 'Physics', 'Programming', 'Database Systems']
        exam_types = [
            Marks.EXAM_INTERNAL,
            Marks.EXAM_ASSIGNMENT,
            Marks.EXAM_MIDTERM,
            Marks.EXAM_FINAL,
        ]

        for i, student in enumerate(created_students):
            for day_offset in range(20):
                att_date = date.today() - timedelta(days=day_offset * 3)
                status = Attendance.STATUS_PRESENT
                if (i + day_offset) % 7 == 0:
                    status = Attendance.STATUS_ABSENT
                elif (i + day_offset) % 5 == 0:
                    status = Attendance.STATUS_LATE
                Attendance.objects.get_or_create(
                    student=student,
                    date=att_date,
                    defaults={'status': status},
                )

            for j, subject in enumerate(subjects):
                for k, exam_type in enumerate(exam_types):
                    base = 60 + (i * 5) + (j * 3)
                    max_m = 100
                    score = min(base + k * 5, max_m)
                    Marks.objects.get_or_create(
                        student=student,
                        subject=subject,
                        exam_type=exam_type,
                        defaults={
                            'marks': score,
                            'max_marks': max_m,
                            'exam_date': date.today() - timedelta(days=30 - k * 7),
                        },
                    )

        self.stdout.write(self.style.SUCCESS('Setup complete!'))
        self.stdout.write('Faculty login: faculty / faculty123')
        self.stdout.write('Student login: cs001 / student123 (or any roll no lowercase)')
