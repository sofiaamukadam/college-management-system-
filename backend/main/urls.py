from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Student
    path('student-login/', views.student_login, name='student_login'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Teacher
    path('teacher-login/', views.teacher_login, name='teacher_login'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # Admin
    path('admin-login/', views.admin_login, name='admin_login'),
    path(
    'admin-dashboard/',
    views.admin_dashboard,
    name='admin_dashboard'
),
   # Attendance
path('attendance/', views.attendance, name='attendance'),
path(
    'subject-attendance/<int:subject_id>/',
    views.subject_attendance,
    name='subject_attendance'
),
path(
    'teacher-attendance/',
    views.teacher_attendance,
    name='teacher_attendance'
),

path(
    'mark-attendance/<int:assignment_id>/',
    views.mark_attendance,
    name='mark_attendance'
),
    # Results
    path(
    'results/',
    views.student_results,
    name='student_results'
),
path('logout/', views.user_logout, name='logout'),
path('student-fees/', views.student_fees, name='student_fees'),
path('student-timetable/', views.student_timetable, name='student_timetable'),
path('student-notifications/',views.student_notifications,name='student_notifications'),
]
