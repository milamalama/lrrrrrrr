import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import AvailabilityForm, FilterForm, ReservationForm
from .models import Equipment, Reservation, ReservationEvent


def event(item, action):
    ReservationEvent.objects.create(reservation=item, reservation_number=item.pk, user=item.user, action=action)


def filtered(request):
    items = Reservation.objects.filter(user=request.user).select_related('equipment')
    form = FilterForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        if data['equipment']:
            items = items.filter(equipment=data['equipment'])
        if data['date']:
            items = items.filter(start__date=data['date'])
        if data['state']:
            items = items.filter(confirmed=data['state'] == 'active')
    return items, form


@login_required
def reservation_list(request):
    items, form = filtered(request)
    return render(request, 'booking/list.html', {'items': items, 'filter_form': form})


@login_required
@transaction.atomic
def reservation_form(request, pk=None):
    item = get_object_or_404(Reservation.objects.select_for_update(), pk=pk, user=request.user, confirmed=True) if pk else Reservation(user=request.user)
    form = ReservationForm(request.POST if request.method == 'POST' else None, instance=item)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        # On PostgreSQL serialize writes for the same device. SQLite has no row locks.
        Equipment.objects.select_for_update().get(pk=obj.equipment_id)
        try:
            obj.full_clean()
        except ValidationError as exc:
            for field, errors in exc.message_dict.items():
                form.add_error(None if field == '__all__' else field, errors)
        else:
            obj.save()
            event(obj, 'Изменена' if pk else 'Создана')
            messages.success(request, 'Бронирование сохранено.')
            return redirect('booking:list')
    return render(request, 'booking/form.html', {'form': form})


@login_required
@require_POST
@transaction.atomic
def reservation_cancel(request, pk):
    item = get_object_or_404(Reservation.objects.select_for_update(), pk=pk, user=request.user)
    if item.confirmed:
        item.confirmed = False
        item.save(update_fields=['confirmed'])
        event(item, 'Отменена')
    return redirect('booking:list')


@login_required
@require_POST
@transaction.atomic
def reservation_delete(request, pk):
    item = get_object_or_404(Reservation.objects.select_for_update(), pk=pk, user=request.user)
    event(item, 'Удалена')
    item.delete()
    return redirect('booking:list')


@login_required
def availability(request):
    form = AvailabilityForm(request.GET if request.GET else None)
    devices = None
    if form.is_bound and form.is_valid():
        data = form.cleaned_data
        occupied = Reservation.objects.filter(confirmed=True, start__lt=data['end'], end__gt=data['start']).values('equipment_id')
        devices = Equipment.objects.filter(is_active=True).exclude(pk__in=occupied)
    return render(request, 'booking/availability.html', {'form': form, 'devices': devices})


@login_required
def history(request):
    events = ReservationEvent.objects.filter(user=request.user)
    return render(request, 'booking/history.html', {'events': events})


@login_required
def export_csv(request):
    items, form = filtered(request)
    if not form.is_valid():
        return HttpResponse('Некорректные параметры фильтра.', status=400)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Номер', 'Устройство', 'Инвентарный номер', 'Начало', 'Конец', 'Цель', 'Состояние'])
    def safe(value):
        value = str(value)
        return "'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value
    for item in items:
        writer.writerow([safe(x) for x in [item.pk, item.equipment.name, item.equipment.inventory_number, timezone.localtime(item.start).isoformat(), timezone.localtime(item.end).isoformat(), item.purpose, 'Действует' if item.confirmed else 'Отменена']])
    return response
