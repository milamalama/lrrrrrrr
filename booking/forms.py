from django import forms
from .models import Equipment, Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ('equipment', 'start', 'end', 'purpose')
        widgets = {field: forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}) for field in ('start', 'end')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment'].queryset = Equipment.objects.filter(is_active=True)
        for field in ('start', 'end'):
            self.fields[field].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']


class FilterForm(forms.Form):
    equipment = forms.ModelChoiceField(
        label='Устройство', queryset=Equipment.objects.all(), required=False,
        empty_label='Все устройства', widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date = forms.DateField(label='Дата начала', required=False, widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}))
    state = forms.ChoiceField(label='Состояние', required=False, choices=[('', 'Все'), ('active', 'Действующие'), ('cancelled', 'Отменённые')], widget=forms.Select(attrs={'class': 'form-select'}))


class AvailabilityForm(forms.Form):
    start = forms.DateTimeField(label='Начало', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), input_formats=['%Y-%m-%dT%H:%M'])
    end = forms.DateTimeField(label='Конец', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), input_formats=['%Y-%m-%dT%H:%M'])

    def clean(self):
        data = super().clean()
        if data.get('start') and data.get('end') and data['end'] <= data['start']:
            self.add_error('end', 'Конец должен быть позже начала.')
        return data
