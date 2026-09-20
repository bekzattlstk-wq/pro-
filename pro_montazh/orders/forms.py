from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    """Создание новой заявки магазином."""

    class Meta:
        model = Order
        fields = ('order_type', 'city', 'street', 'house', 'comment', 'date_from', 'date_to')
        widgets = {
            'date_from': forms.DateInput(attrs={'type': 'date'}),
            'date_to': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        self.store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)
        self.fields['city'].required = True
        self.fields['street'].required = True
        self.fields['house'].required = True
        if self.store and not self.is_bound:
            self.fields['city'].initial = self.store.city
            self.fields['street'].initial = self.store.street
            self.fields['house'].initial = self.store.house

    def clean(self):
        cleaned = super().clean()
        date_from, date_to = cleaned.get('date_from'), cleaned.get('date_to')
        if date_from and date_to and date_to < date_from:
            self.add_error('date_to', "Дата окончания не может быть раньше даты начала.")
        return cleaned
