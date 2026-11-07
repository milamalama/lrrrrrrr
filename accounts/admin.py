from django.contrib import admin
from .models import AcademicGroup, Course, Department, StudentProfile

@admin.register(AcademicGroup)
class AcademicGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department')
    list_filter = ('department',)
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department')
    list_filter = ('department',)
    search_fields = ('title',)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department', 'academic_group')
    list_filter = ('department', 'academic_group')