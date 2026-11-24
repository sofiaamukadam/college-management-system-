from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout 
from .models import Student, Teacher, Attendance, Result, TeachingAssignment, Class, Subject, Exam, StudentFee,Timetable, StudentNotification
from datetime import timedelta, date
def user_logout(request):
    logout(request)
    return redirect('/')

def home(request):
    return render(request, 'home.html')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('/admin-dashboard/')

        return render(request, 'login/admin_login.html', {
            'error': 'Invalid admin credentials'
        })

    return render(request, 'login/admin_login.html')

def student_login(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        password = request.POST.get('password')

        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            return render(request, 'login/student_login.html', {
                'error': 'Student ID not found'
            })

        user = authenticate(
            request,
            username=student.user.username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')

        return render(request, 'login/student_login.html', {
            'error': 'Invalid password'
        })

    return render(request, 'login/student_login.html')

def teacher_login(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        password = request.POST.get('password')

        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
        except Teacher.DoesNotExist:
            return render(request, 'login/teacher_login.html', {
                'error': 'Teacher ID not found'
            })

        user = authenticate(
            request,
            username=teacher.user.username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('/teacher-dashboard/')

        return render(request, 'login/teacher_login.html', {
            'error': 'Invalid password'
        })

    return render(request, 'login/teacher_login.html')

@login_required
def dashboard(request):
    student = Student.objects.get(user=request.user)

    attendances = Attendance.objects.filter(student=student)

    total_classes = attendances.count()
    present_classes = attendances.filter(status="Present").count()

    if total_classes > 0:
        attendance_percentage = round(
            (present_classes / total_classes) * 100,
        )
    else:
        attendance_percentage = 0

    fees = StudentFee.objects.filter(
        student=student
    ).order_by('-fee_structure__academic_year')
    notifications = StudentNotification.objects.filter(
    student=student
    ).select_related(
    'notification'
    ).order_by('-notification__created_at')

    return render(request, 'dashboard.html', {
        'student': student,
        'attendance_percentage': attendance_percentage,
        'fees': fees,
        'notifications': notifications,
    })

@login_required
def attendance(request):

    student = Student.objects.get(user=request.user)

    attendance_records = Attendance.objects.filter(
        student=student
    ).select_related(
        'teaching_assignment__subject',
        'teaching_assignment__teacher'
    ).order_by(
        '-date',
        'lecture_number'
    )

    # ==========================================
    # OVERALL ATTENDANCE
    # ==========================================

    total_lectures = attendance_records.count()

    attended_lectures = attendance_records.filter(
        status='Present'
    ).count()

    missed_lectures = attendance_records.filter(
        status='Absent'
    ).count()

    if total_lectures > 0:

        overall_percentage = round(
            (attended_lectures / total_lectures) * 100,
            1
        )

    else:

        overall_percentage = 0


    # ==========================================
    # SUBJECT-WISE ATTENDANCE
    # ==========================================

    subjects = {}

    for record in attendance_records:

        subject = record.teaching_assignment.subject

        if subject.id not in subjects:

            subjects[subject.id] = {
                'id': subject.id,
                'code': subject.subject_code,
                'name': subject.name,
                'total': 0,
                'attended': 0,
                'missed': 0,
                'percentage': 0,
                'lectures_needed': 0
            }

        subjects[subject.id]['total'] += 1

        if record.status == 'Present':

            subjects[subject.id]['attended'] += 1

        else:

            subjects[subject.id]['missed'] += 1


    # ==========================================
    # SUBJECT PERCENTAGE + LECTURES NEEDED
    # ==========================================

    for subject in subjects.values():

        if subject['total'] > 0:

            subject['percentage'] = round(
                (
                    subject['attended']
                    / subject['total']
                ) * 100,
                1
            )

            # Calculate lectures required
            # to reach 75% attendance

            if subject['percentage'] < 75:

                needed = 0

                while (
                    (
                        subject['attended'] + needed
                    )
                    /
                    (
                        subject['total'] + needed
                    )
                ) < 0.75:

                    needed += 1

                subject['lectures_needed'] = needed


    # ==========================================
    # ATTENDANCE STREAK
    # ==========================================

    present_dates = set()

    for record in attendance_records:

        if record.status == 'Present':

            present_dates.add(record.date)


    present_dates = sorted(
        present_dates,
        reverse=True
    )


    current_streak = 0
    streak_warning = False
    streak_broken = False


    if present_dates:

        today = attendance_records.first().date

        latest_date = present_dates[0]


        # Check how long since last attendance

        latest_gap = (
            today - latest_date
        ).days


        # If two or more calendar days
        # have passed without attendance,
        # streak is broken.

        if latest_gap >= 2:

            streak_broken = True
            current_streak = 0

        else:

            # Latest attendance is today
            # or yesterday.

            if latest_gap == 1:

                streak_warning = True


            current_streak = 1


            # Check previous attendance days

            for i in range(1, len(present_dates)):

                previous_date = present_dates[i - 1]

                current_date = present_dates[i]

                gap = (
                    previous_date - current_date
                ).days


                # Consecutive calendar day
                # OR one-day grace gap

                if gap == 1:

                    current_streak += 1

                elif gap == 2:

                    current_streak += 1

                    streak_warning = True

                else:

                    break


    # ==========================================
    # SEND DATA TO HTML
    # ==========================================

    return render(
        request,
        'modules/attendance.html',
        {
            'student': student,

            'attendance_records': attendance_records,

            # Overall
            'total_lectures': total_lectures,
            'attended_lectures': attended_lectures,
            'missed_lectures': missed_lectures,
            'overall_percentage': overall_percentage,

            # Subjects
            'subjects': subjects.values(),

            # Streak
            'current_streak': current_streak,
            'streak_warning': streak_warning,
            'streak_broken': streak_broken,
        }
    )
@login_required
def student_results(request):
    student = Student.objects.get(user__username='student1')
    results = Result.objects.filter(
        student=student
    ).select_related(
        'exam__subject',
        'exam__class_name'
    )

    return render(
        request,
        'modules/student_results.html',
        {
            'student': student,
            'results': results
        }
    )
    
@login_required
def teacher_dashboard(request):
    teacher = Teacher.objects.get(user=request.user)

    return render(request, 'teacher_dashboard.html', {
        'teacher': teacher
    })

@login_required
def teacher_attendance(request):
    teacher = Teacher.objects.get(user=request.user)

    assignments = TeachingAssignment.objects.filter(
        teacher=teacher
    ).select_related(
        'class_name',
        'subject'
    )

    return render(
        request,
        'modules/teacher_attendance.html',
        {
            'teacher': teacher,
            'assignments': assignments
        }
    )
@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
def mark_attendance(request, assignment_id):

    teacher = Teacher.objects.get(user=request.user)

    assignment = TeachingAssignment.objects.get(
        id=assignment_id,
        teacher=teacher
    )

    students = Student.objects.filter(
        class_name=assignment.class_name
    ).order_by('student_id')

    if request.method == 'POST':

        attendance_date = request.POST.get('attendance_date')
        lecture_number = request.POST.get('lecture_number')

        for student in students:

            status = request.POST.get(
                f'status_{student.id}'
            )

            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    teaching_assignment=assignment,
                    date=attendance_date,
                    lecture_number=lecture_number,
                    defaults={
                        'status': status
                    }
                )

        return redirect('teacher_attendance')

    return render(
        request,
        'modules/mark_attendance.html',
        {
            'assignment': assignment,
            'students': students
        }
    )
@login_required
def subject_attendance(request, subject_id):

    student = Student.objects.get(user=request.user)

    subject = Subject.objects.get(
        id=subject_id
    )

    attendance_records = Attendance.objects.filter(
        student=student,
        teaching_assignment__subject=subject
    ).select_related(
        'teaching_assignment__teacher'
    ).order_by(
        '-date',
        'lecture_number'
    )

    # Total lectures
    total_lectures = attendance_records.count()

    # Attended lectures
    attended_lectures = attendance_records.filter(
        status='Present'
    ).count()

    # Missed lectures
    missed_lectures = attendance_records.filter(
        status='Absent'
    ).count()

    # Percentage
    if total_lectures > 0:
        percentage = round(
            (attended_lectures / total_lectures) * 100,
            1
        )
    else:
        percentage = 0

    # Lectures needed to reach 75%
    lectures_needed = 0

    if percentage < 75 and total_lectures > 0:

        while (
            (attended_lectures + lectures_needed)
            / (total_lectures + lectures_needed)
        ) < 0.75:

            lectures_needed += 1

    return render(
        request,
        'modules/subject_attendance.html',
        {
            'student': student,
            'subject': subject,
            'attendance_records': attendance_records,

            'total_lectures': total_lectures,
            'attended_lectures': attended_lectures,
            'missed_lectures': missed_lectures,
            'percentage': percentage,
            'lectures_needed': lectures_needed,
        }
    )
@login_required
def student_fees(request):
    student = Student.objects.get(user=request.user)

    fees = StudentFee.objects.filter(
        student=student
    ).select_related('fee_structure')

    return render(request, 'student_fees.html', {
        'student': student,
        'fees': fees
    })
@login_required
def student_timetable(request):

    student = Student.objects.get(user=request.user)

    timetable = Timetable.objects.filter(
        teaching_assignment__class_name=student.class_name
    ).select_related(
        'teaching_assignment__subject',
        'teaching_assignment__teacher',
        'teaching_assignment__class_name'
    ).order_by('day', 'start_time')

    return render(request, 'student_timetable.html', {
        'student': student,
        'timetable': timetable,
    })

@login_required
def student_notifications(request):
    student = Student.objects.get(user=request.user)

    notifications = StudentNotification.objects.filter(
        student=student
    ).select_related(
        'notification'
    ).order_by('-notification__created_at')

    return render(request, 'student_notifications.html', {
        'student': student,
        'notifications': notifications,
    })
    