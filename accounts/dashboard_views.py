import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

from .models import (
    Department,
    Course,
    AcademicGroup,
    StudentProfile,
)


def _rows(department_id=None):
    departments = Department.objects.all().order_by('name')

    if department_id:
        departments = departments.filter(pk=department_id)

    departments = departments.annotate(
        courses_count=Count('courses', distinct=True),
        groups_count=Count('groups', distinct=True),
        students_count=Count('students', distinct=True),
    )

    return list(
        departments.values(
            'id',
            'name',
            'courses_count',
            'groups_count',
            'students_count',
        )
    )


def _department_filter(request):
    raw = request.GET.get('department', '').strip()

    if raw.isdecimal():
        department_id = int(raw)

        if Department.objects.filter(pk=department_id).exists():
            return department_id

    return None


def _payload(request):
    department_id = _department_filter(request)

    departments = _rows(department_id)

    courses = Course.objects.all()
    groups = AcademicGroup.objects.all()
    students = StudentProfile.objects.all()

    if department_id:
        courses = courses.filter(department_id=department_id)
        groups = groups.filter(department_id=department_id)
        students = students.filter(department_id=department_id)

    group_rows = list(
        groups.annotate(
            students_count=Count('students', distinct=True)
        )
        .order_by('name')
        .values(
            'id',
            'name',
            'department__name',
            'students_count',
        )
    )

    assigned_students = students.filter(
        academic_group__isnull=False
    ).count()

    groups_count = groups.count()

    average_group_size = (
        round(assigned_students / groups_count, 1)
        if groups_count > 0
        else 0
    )

    largest_group = max(
        group_rows,
        key=lambda row: row['students_count'],
        default=None,
    )

    top_department = max(
        departments,
        key=lambda row: row['students_count'],
        default=None,
    )

    students_without_group = students.filter(
        academic_group__isnull=True
    ).count()

    course_rows = list(
        courses.annotate(
            students_count=Count('students', distinct=True)
        )
        .order_by('title')
        .values(
            'id',
            'title',
            'department__name',
            'students_count',
        )
    )

    return {
        'filter': {
            'department': department_id,
        },

        'summary': {
            'departments': len(departments),
            'courses': courses.count(),
            'groups': groups_count,
            'students': students.count(),
        },

        'departments': departments,

        'groups': group_rows,

        'courses': course_rows,

        'extra': {
            'average_group_size': average_group_size,

            'largest_group': {
                'name': largest_group['name'],
                'students': largest_group['students_count'],
            } if largest_group else None,

            'top_department': {
                'name': top_department['name'],
                'students': top_department['students_count'],
            } if top_department else None,

            'students_without_group': students_without_group,

            'assigned_students': assigned_students,
        },
    }


@login_required
def dashboard_page(request, section='overview'):
    if section not in ('overview', 'departments', 'groups'):
        section = 'overview'

    return render(
        request,
        'accounts/dashboard/index.html',
        {
            'section': section,
            'departments': Department.objects.order_by('name').values(
                'id',
                'name',
            ),
        },
    )


@login_required
def dashboard_api(request):
    data = _payload(request)
    response = JsonResponse(
        data,
        json_dumps_params={
            'ensure_ascii': False,
        },
    )
    response['Cache-Control'] = 'no-store'
    return response
