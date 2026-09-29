from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class BootstrapFormMixin:
    """Adds Bootstrap 5 classes to every widget and uses native date/time inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.RadioSelect):
                continue
            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = (widget.attrs.get('class', '') + ' ' + css).strip()
            if isinstance(widget, forms.DateInput):
                widget.input_type = 'date'
                widget.format = '%Y-%m-%d'
            elif isinstance(widget, forms.TimeInput):
                widget.input_type = 'time'
                widget.format = '%H:%M'


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class ChangePasswordForm(BootstrapFormMixin, PasswordChangeForm):
    pass
