from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Investor, Artifact, EmailDraft, CommunicationLog, ResponseFunding


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class InvestorForm(forms.ModelForm):
    """Form for creating/editing investors."""
    
    class Meta:
        model = Investor
        fields = ['name', 'email', 'labels', 'address', 'details', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter investor name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter email address'
            }),
            'labels': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., VC, Tech, Series-A (comma separated)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter address',
                'rows': 3
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Additional details about the investor',
                'rows': 4
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Amount in Rs.'
            }),
        }


class ArtifactForm(forms.ModelForm):
    """Form for uploading artifacts."""
    
    class Meta:
        model = Artifact
        fields = ['name', 'artifact_type', 'artifact_labels', 'file', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter artifact name'
            }),
            'artifact_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'artifact_labels': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., pitchdeck, financial, demo (comma separated)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-file'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Describe this artifact',
                'rows': 3
            }),
        }


class EmailDraftForm(forms.ModelForm):
    """Form for creating email drafts."""
    
    class Meta:
        model = EmailDraft
        fields = ['name', 'subject', 'body', 'artifacts']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Unique draft name (e.g., pitchdeck, intro_email)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Email subject line'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Email body content (supports HTML)',
                'rows': 10
            }),
            'artifacts': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-checkbox-group'
            }),
        }


class ResponseFundingForm(forms.ModelForm):
    """Form for recording investor responses."""
    
    class Meta:
        model = ResponseFunding
        fields = ['communication', 'investor', 'response_status', 'amount_offered', 'notes', 'response_date']
        widgets = {
            'communication': forms.Select(attrs={
                'class': 'form-select'
            }),
            'investor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'response_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount_offered': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Amount offered in Rs.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Notes about the response',
                'rows': 4
            }),
            'response_date': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            }),
        }


class ChatbotForm(forms.Form):
    """Form for chatbot input."""
    message = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'chatbot-input',
            'placeholder': 'Type your command here...',
            'autocomplete': 'off'
        })
    )
