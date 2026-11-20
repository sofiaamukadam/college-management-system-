from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Class(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student_id} - {self.name}"

class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    teacher_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return f"{self.teacher_id} - {self.name}"

class Subject(models.Model):
    subject_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subject_code} - {self.name}"

class TeachingAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher.name} - {self.class_name.name} - {self.subject.name}"   
class Timetable(models.Model):

    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]

    teaching_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE
    )

    day = models.CharField(
        max_length=10,
        choices=DAY_CHOICES
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    classroom = models.CharField(max_length=50)

    def __str__(self):
        return (
            f"{self.day} - "
            f"{self.teaching_assignment.subject.name} - "
            f"{self.start_time}"
        )
class Notification(models.Model):

    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('Exam', 'Exam'),
        ('Result', 'Result'),
        ('Attendance', 'Attendance'),
        ('Fees', 'Fees'),
        ('Timetable', 'Timetable'),
        ('Announcement', 'Announcement'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='General'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    target_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title

class StudentNotification(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'notification'],
                name='unique_student_notification'
            )
        ]

    def __str__(self):
        return f"{self.student.name} - {self.notification.title}"
        
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    teaching_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    lecture_number = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    def __str__(self):
        return (
            f"{self.student.name} - "
            f"{self.date} - "
            f"Lecture {self.lecture_number} - "
            f"{self.status}"
        )
class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ('Internal', 'Internal'),
        ('University', 'University'),
    ]

    exam_name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    exam_date = models.DateField()
    total_marks = models.IntegerField(default=100)

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default='Internal'
    )

    passing_marks = models.PositiveIntegerField(default=40)

    academic_year = models.CharField(
        max_length=9,
        blank=True,
        default=""
    )

    is_final = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.exam_name} - {self.subject.name}"

def calculate_fees(self):
    # Calculate regular fees
    self.regular_fee = (
        self.fee_structure.tuition_fee
        + self.fee_structure.library_fee
        + self.fee_structure.examination_fee
        + self.fee_structure.other_fee
    )

    # Find failed subjects in final university examinations
    failed_subjects = Result.objects.filter(
        student=self.student,
        exam__exam_type='University',
        exam__is_final=True,
        exam__academic_year=self.fee_structure.academic_year,
        marks_obtained__lt=models.F('exam__passing_marks')
    ).values_list('exam__subject_id', flat=True).distinct()

    # Calculate KT fees
    self.kt_subject_count = failed_subjects.count()

    self.kt_fee = (
        self.kt_subject_count
        * self.fee_structure.kt_fee_per_subject
    )

    # Calculate total
    self.total_fee = self.regular_fee + self.kt_fee

class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    marks_obtained = models.IntegerField()

    def __str__(self):
        return f"{self.student.name} - {self.exam.exam_name}"

class FeeStructure(models.Model):
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)

    tuition_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    library_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    examination_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    other_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    kt_fee_per_subject = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['class_name', 'academic_year'],
                name='unique_class_fee_year'
            )
        ]

    def __str__(self):
        return f"{self.class_name.name} - {self.academic_year}"


class StudentFee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(
        FeeStructure, on_delete=models.CASCADE
    )

    regular_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    kt_subject_count = models.PositiveIntegerField(default=0)
    kt_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    total_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    def calculate_fees(self):
        self.regular_fee = (
            self.fee_structure.tuition_fee
            + self.fee_structure.library_fee
            + self.fee_structure.examination_fee
            + self.fee_structure.other_fee
        )

        failed_subjects = Result.objects.filter(
            student=self.student,
            exam__exam_type='University',
            exam__is_final=True,
            exam__academic_year=self.fee_structure.academic_year,
            marks_obtained__lt=models.F('exam__passing_marks')
        ).values_list('exam__subject_id', flat=True).distinct()

        self.kt_subject_count = failed_subjects.count()

        self.kt_fee = (
            self.kt_subject_count
            * self.fee_structure.kt_fee_per_subject
        )

        self.total_fee = self.regular_fee + self.kt_fee

    @property
    def amount_paid(self):
        total = self.payments.aggregate(
            total=models.Sum('amount')
        )['total']
        return total or Decimal('0.00')

    @property
    def balance(self):
        return max(
            Decimal('0.00'),
            self.total_fee - self.amount_paid
        )

    @property
    def payment_status(self):
        if self.amount_paid >= self.total_fee:
            return "Paid"
        elif self.amount_paid > 0:
            return "Partial"
        return "Pending"

    def __str__(self):
        return f"{self.student.name} - {self.fee_structure.academic_year}"
class FeePayment(models.Model):
    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    transaction_id = models.CharField(
        max_length=100, blank=True
    )
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student_fee.student.name} - ₹{self.amount}"  
@receiver(post_save, sender=Result)
@receiver(post_delete, sender=Result)
def update_student_fees(sender, instance, **kwargs):

    exam_year = instance.exam.academic_year

    student_fees = StudentFee.objects.filter(
        student=instance.student,
        fee_structure__academic_year=exam_year
    )

    for fee in student_fees:
        fee.calculate_fees()

        fee.save(update_fields=[
            'regular_fee',
            'kt_subject_count',
            'kt_fee',
            'total_fee'
        ])
