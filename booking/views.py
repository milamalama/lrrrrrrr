from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ReservationForm
from .models import Equipment, Reservation


@login_required
def reservation_list(request):
    items = Reservation.objects.filter(
        user=request.user
    )

    equipment_id = request.GET.get("equipment")

    if equipment_id:
        items = items.filter(
            equipment_id=equipment_id
        )

    items = items.select_related(
        "equipment"
    ).order_by("start")

    equipment_list = Equipment.objects.all()

    return render(
        request,
        "booking/list.html",
        {
            "items": items,
            "equipment_list": equipment_list,
            "selected_equipment": equipment_id,
        }
    )


@login_required
def reservation_create(request):
    form = ReservationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()

        return redirect("reservation_list")

    return render(
        request,
        "booking/form.html",
        {"form": form}
    )


@login_required
def reservation_edit(request, pk):
    item = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user
    )

    form = ReservationForm(
        request.POST or None,
        instance=item
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("reservation_list")

    return render(
        request,
        "booking/form.html",
        {"form": form}
    )


@login_required
@require_POST
def reservation_delete(request, pk):
    item = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user
    )

    item.delete()
    return redirect("reservation_list")

@login_required
@require_POST
def reservation_cancel(request, pk):
    item = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user
    )

    item.confirmed = False
    item.save(update_fields=["confirmed"])

    return redirect("reservation_list")
