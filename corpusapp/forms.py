from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserInfo

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = UserInfo
        fields = UserCreationForm.Meta.fields + ('email',)