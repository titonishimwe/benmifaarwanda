from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
            })


class AdminMemberForm(RegisterForm):
    """Staff-only form to register platform members."""

    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(max_length=20, required=False, label='Phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'e.g. +250 788 000 000'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.username.lower()
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
            profile = user.profile
            phone = self.cleaned_data.get('phone_number', '')
            if phone:
                profile.phone_number = phone
                profile.save(update_fields=['phone_number'])
        return user


class AdminEditMemberForm(forms.Form):
    """Staff-only: change a member's username and optionally reset password."""

    user_id = forms.IntegerField(widget=forms.HiddenInput())
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(
        required=False,
        label='New password',
        widget=forms.PasswordInput(render_value=False),
    )
    password2 = forms.CharField(
        required=False,
        label='Confirm new password',
        widget=forms.PasswordInput(render_value=False),
    )

    def __init__(self, *args, target_user=None, **kwargs):
        self.target_user = target_user
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'user_id':
                continue
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['username'].widget.attrs.setdefault('autocomplete', 'username')
        self.fields['password1'].widget.attrs.setdefault('autocomplete', 'new-password')
        self.fields['password2'].widget.attrs.setdefault('autocomplete', 'new-password')
        if target_user and not self.is_bound:
            self.fields['user_id'].initial = target_user.pk
            self.fields['username'].initial = target_user.username

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip().lower()
        if not username:
            raise ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if self.target_user:
            qs = qs.exclude(pk=self.target_user.pk)
        if qs.exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1') or ''
        password2 = cleaned.get('password2') or ''
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match.')
            elif self.target_user:
                password_validation.validate_password(password1, self.target_user)
        return cleaned

    def save(self):
        if not self.target_user:
            raise ValidationError('No member selected.')
        user = self.target_user
        user.username = self.cleaned_data['username']
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        user.save()
        return user
