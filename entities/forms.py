from django import forms

class CreateGroupForm(forms.Form):
    name = forms.CharField(label="Название", max_length=30, required=True)
    sort = forms.CharField(label="Сортировка (0 - не отображать на главной странице)", max_length=30, required=False)
    
class CreateEntityForm(forms.Form):
    name = forms.CharField(
        label="Название сущности",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название'})
    )
    sort = forms.CharField(
        label="Сортировка (0 - не отображать на главной странице)",
        max_length=30,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите число'})
    )
    
    
