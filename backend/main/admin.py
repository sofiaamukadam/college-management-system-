from django.contrib import admin
from .models import (
    Class,
    Student,
    Teacher,
    Subject,
    TeachingAssignment,
    Attendance,
    Exam,
    Result,
    FeeStructure,
    StudentFee,
    FeePayment,
    Timetable,
    Notification,
    StudentNotification
)


admin.site.register(Class)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(TeachingAssignment)
admin.site.register(Attendance)
admin.site.register(Exam)
admin.site.register(Result)
admin.site.register(FeeStructure)


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'fee_structure',
        'regular_fee',
        'kt_subject_count',
        'kt_fee',
        'total_fee',
        'amount_paid',
        'balance',
        'payment_status',
    )

    readonly_fields = (
        'regular_fee',
        'kt_subject_count',
        'kt_fee',
        'total_fee',
    )

    def save_model(self, request, obj, form, change):
        obj.calculate_fees()
        super().save_model(request, obj, form, change)


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):

    list_display = (
        'student_fee',
        'amount',
        'payment_date',
        'transaction_id',
    )
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = (
        'day',
        'teaching_assignment',
        'start_time',
        'end_time',
        'classroom',
    )

    list_filter = ('day',)
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'target_class', 'created_at')
    list_filter = ('category', 'target_class')
    search_fields = ('title', 'message')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.target_class:
            students = Student.objects.filter(
                class_name=obj.target_class
            )
        else:
            students = Student.objects.all()

        for student in students:
            StudentNotification.objects.get_or_create(
                student=student,
                notification=obj
            )

@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    list_display = ('student', 'notification', 'is_read', 'read_at')
    list_filter = ('is_read',)
    search_fields = ('student__name', 'notification__title')