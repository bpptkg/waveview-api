from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from waveview.users.models import User


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "name",
            "bio",
            "is_staff",
            "is_active",
            "is_superuser",
        )
