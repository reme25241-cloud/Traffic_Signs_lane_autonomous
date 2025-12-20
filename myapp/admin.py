# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'gender')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('name', 'contact', 'age', 'gender')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)


from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'resolved']
    list_filter = ['resolved']
    search_fields = ['user__name', 'message']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'timestamp', 'is_group_message')
    search_fields = ('sender__email', 'receiver__email', 'text')
    list_filter = ('is_group_message', 'timestamp')
    readonly_fields = ('timestamp',)
    

# mainApplicationFunctionality20240625
# from .models import PatientData

# @admin.register(PatientData)
# class PatientDataAdmin(admin.ModelAdmin):
#     list_display = ['user', 'age', 'blood_pressure', 'predicted_diseases', 'created_at']
#     list_filter = ['created_at', 'predicted_diseases', 'smoking', 'alcohol']
#     search_fields = ['user__username', 'predicted_diseases']
