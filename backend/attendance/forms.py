from django import forms
from datetime import time


class WeekTimetableForm(forms.Form):
    WEEKDAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    week_start_date = forms.DateField(
        help_text="Select the Monday (or any start date) for the week.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    days_to_create = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        initial=[0, 1, 2, 3, 4],
        widget=forms.CheckboxSelectMultiple,
        help_text="Choose which weekdays to create sessions for.",
    )
    daily_session_names = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "cols": 40}),
        help_text="Enter session names, one per line. Optional: 'Name | HH:MM | HH:MM' to specify start/end times.",
        initial="Math | 09:00 | 10:00\nPhysics | 10:15 | 11:15\nLunch\nChemistry"
    )
    first_session_start_time = forms.TimeField(initial=time(9, 0), widget=forms.TimeInput(attrs={"type": "time"}))
    session_duration_minutes = forms.IntegerField(min_value=10, max_value=600, initial=60)
    break_minutes_between_sessions = forms.IntegerField(min_value=0, max_value=180, initial=10)
    is_active = forms.BooleanField(required=False, initial=True)
