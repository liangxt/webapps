from django import forms

from tragether.models import *
from tragether.choice import *

import re
import pytz
import datetime


class InvitationForm(forms.Form):
    receiver = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'), required=True)
    subject = forms.CharField(max_length=42, required=True)
    content = forms.CharField(max_length=2048, widget=forms.Textarea(attrs={'cols': 20, 'rows': 5}), required=True)

    def __init__(self, *args, **kwargs):
        super(InvitationForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'id': 'invite_id_content'})
        for fieldname in ['subject', 'content', 'receiver']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class PollForm(forms.Form):
    choose = forms.ChoiceField()

    def __init__(self, poll, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        choices = poll.attraction.all()
        self.fields['choose'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                  choices=[(choice.id, str(choice)) for choice in choices],
                                                  label='')


class AddAttractionForm(forms.Form):
    name = forms.CharField(max_length=30, label='')

    def __init__(self, *args, **kwargs):
        super(AddAttractionForm, self).__init__(*args, **kwargs)
        self.fields['name'].help_text = None
        self.fields['name'].widget.attrs.update({'placeholder': 'Add new...', 'id': 'attraction_content'})


class ApplicationForm(forms.Form):
    subject = forms.CharField(max_length=42)
    content = forms.CharField(max_length=2048, widget=forms.Textarea(attrs={'cols': 20, 'rows': 10}))

    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        for fieldname in ['subject', 'content']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})

            
class DateInput(forms.DateInput):
    input_type = 'date'


class CreateTravelForm(forms.ModelForm):

    class Meta:
        model = Travel
        exclude = ['creator', ]
        widgets = {
            'start_time': DateInput(),
            'end_time': DateInput(),
        }

    def clean(self):
        cleaned_data = super(CreateTravelForm, self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and start_time > end_time:
            raise forms.ValidationError("End time should be later than start time.")
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(CreateTravelForm, self).__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'dropdown theme-dropdown clearfix form-control'})
        self.fields['status'].help_text = None
        self.fields['info'].label = 'Other information'
        self.fields['budget'].label = 'Individual budget'
        for fieldname in ['start_time', 'end_time', 'destination', 'group_size', 'budget', 'info']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class EditUserInforForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = {'first_name', 'last_name', 'password'}

    def __init__(self, *args, **kwargs):
        super(EditUserInforForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        for fieldname in ['first_name', 'last_name', 'password']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class EditProfileForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = {'age', 'bio', 'picture'}
        widgets = {'picture': forms.FileInput()}

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)

        for fieldname in ['age', 'bio']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=20, 
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}))
    first_name = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-control'}))
    email = forms.EmailField(max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'}))
    gender = forms.CharField(max_length=1,
        required=True,
        widget=forms.Select(choices=(('', 'Select gender:'),)+GENDER_CHOICES, attrs={'class': 'form-control'}))
    #age = forms.IntegerField(min_value=0, 
    #    max_value=125, 
    #    required=False, 
    #    widget=forms.TextInput(attrs={'placeholder': 'Age (Optional)', 'class': 'form-control'}))
    #bio = forms.CharField(max_length=420, 
    #    required=False, 
    #    widget=forms.Textarea(attrs={'rows':5, 'placeholder': 'Bio (Optional)', 'class': 'form-control'}))
    password1 = forms.CharField(max_length=50, 
        label='Password', 
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}))
    password2 = forms.CharField(max_length=50, 
        label='Confirm password', 
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password', 'class': 'form-control'}))

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")
        if not re.match(r"^[\w@+\.-]+$", username):
            raise forms.ValidationError("Username must only contain letters, numbers, _ , @, +, . and -.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__exact=email):
            raise forms.ValidationError("Email already exists.")
        return email

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if not (gender == "F" or gender == "M"):
            raise forms.ValidationError("Please don't change the value, thanks!")
        return gender


class EmailForm(forms.Form):
    email = forms.EmailField(max_length=50, 
        widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email__exact=email):
            raise forms.ValidationError("Email doesn't exist.")
        if not User.objects.get(email__exact=email).is_active:
            raise forms.ValidationError("Email hasn't been confirmed.")
        return email
        

class PSWDForm(forms.Form):
    password1 = forms.CharField(max_length=50, 
                                label='Password', 
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}))
    password2 = forms.CharField(max_length=50, 
                                label='Confirm password',  
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password', 'class': 'form-control'}))

    def clean(self):
        cleaned_data = super(PSWDForm, self).clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")
        return cleaned_data  


class SearchGroupForm(forms.Form):
    destination = forms.CharField(required=False, max_length=40, 
        widget=forms.TextInput(attrs={'placeholder': 'Destination', 'class': 'form-control'}))
    start_time = forms.DateField(required=False, widget=forms.DateInput(attrs={'placeholder': 'Select start date', 'class': 'form-control'}))
    end_time = forms.DateField(required=False, widget=forms.DateInput(attrs={'placeholder': 'Select end date', 'class': 'form-control'}))

    def clean(self):
        cleaned_data = super(SearchGroupForm, self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and start_time > end_time:
            raise forms.ValidationError("End time should be later than start time.")
        return self.cleaned_data


class ChatboxForm(forms.ModelForm):
    content = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Chat with other members...', 'class': 'form-control input-sm'}))

    class Meta:
        model = Chatbox_Messages
        fields = ('content', )


class ItineraryForm(forms.ModelForm):
    place = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Place', 'class': 'form-control'}))
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'placeholder': 'Select start time', 'class': 'form-control', 'id': 'itinerary-datetimepicker'}))

    class Meta:
        model = Itinerary
        fields = ('place', 'start_time', )

    def clean_start_time(self):
        cleaned_data = super(ItineraryForm, self).clean()
        start_time = cleaned_data.get('start_time')
        local_tz = pytz.timezone('US/Eastern')
        if start_time < local_tz.localize(datetime.datetime(1990, 1, 1, 0, 0)):
            raise forms.ValidationError("Start time should be later than year 1990.")
        return start_time
