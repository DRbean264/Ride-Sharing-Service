from datetime import date, time, datetime
from django import forms
from django.forms import DateTimeInput


class BootstrapDateTimePickerInput(DateTimeInput):
    template_name = 'rideshare/bootstrap_datetimepicker.html'

    def get_context(self, name, value, attrs):
        datetimepicker_id = 'datetimepicker_{name}'.format(name=name)
        if attrs is None:
            attrs = dict()
        attrs['data-target'] = '#{id}'.format(id=datetimepicker_id)
        attrs['class'] = 'form-control datetimepicker-input'
        context = super().get_context(name, value, attrs)
        context['widget']['datetimepicker_id'] = datetimepicker_id
        return context


class DateSelectorWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        seconds = [(second, second) for second in range(0, 60)]
        minutes = [(minute, minute) for minute in range(0, 60)]
        hours = [(hour, hour) for hour in range(0, 24)]
        days = [(day, day) for day in range(1, 32)]
        months = [(month, month) for month in range(1, 13)]
        years = [(year, year) for year in range(2022, 2025)]
        widgets = [
            forms.Select(attrs=attrs, choices=months),
            forms.Select(attrs=attrs, choices=days),
            forms.Select(attrs=attrs, choices=years),
            forms.Select(attrs=attrs, choices=hours),
            forms.Select(attrs=attrs, choices=minutes),
            forms.Select(attrs=attrs, choices=seconds),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, datetime):
            return [value.month, value.day, value.year,
                    value.hour, value.minute, value.second]
        return [None, None, None, None, None, None]

    def value_from_datadict(self, data, files, name):
        month, day, year, hour, minute, second = super().value_from_datadict(data, files, name)
        # DateField expects a single string that it can parse into a date.
        return '{}-{}-{} {}:{}:{}'.format(year, month, day, hour, minute, second)
