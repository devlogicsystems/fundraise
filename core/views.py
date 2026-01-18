from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import Investor, Artifact, EmailDraft, CommunicationLog, ResponseFunding
from .forms import (
    InvestorForm, ArtifactForm, EmailDraftForm, 
    ResponseFundingForm, UserRegistrationForm, ChatbotForm
)
from .chatbot import ChatbotService


# ==================== Authentication Views ====================

def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ==================== Dashboard View ====================

@login_required
def dashboard(request):
    """Main dashboard with analytics and chatbot."""
    now = timezone.now()
    
    # Basic stats
    total_investors = Investor.objects.count()
    total_artifacts = Artifact.objects.count()
    total_drafts = EmailDraft.objects.count()
    total_emails_sent = CommunicationLog.objects.filter(status='success').count()
    
    # Email aging analysis
    emails_7_days = CommunicationLog.objects.filter(
        sent_at__gte=now - timedelta(days=7),
        status='success'
    ).count()
    
    emails_15_days = CommunicationLog.objects.filter(
        sent_at__gte=now - timedelta(days=15),
        sent_at__lt=now - timedelta(days=7),
        status='success'
    ).count()
    
    emails_30_days = CommunicationLog.objects.filter(
        sent_at__gte=now - timedelta(days=30),
        sent_at__lt=now - timedelta(days=15),
        status='success'
    ).count()
    
    emails_older = CommunicationLog.objects.filter(
        sent_at__lt=now - timedelta(days=30),
        status='success'
    ).count()
    
    # Response/Funding analytics
    response_stats = ResponseFunding.objects.values('response_status').annotate(
        count=Count('id'),
        total_amount=Sum('amount_offered')
    )
    
    response_data = {
        'success': {'count': 0, 'amount': 0},
        'failure': {'count': 0, 'amount': 0},
        'pending': {'count': 0, 'amount': 0},
    }
    
    for stat in response_stats:
        status = stat['response_status']
        response_data[status] = {
            'count': stat['count'],
            'amount': stat['total_amount'] or 0
        }
    
    # Recent communications
    recent_communications = CommunicationLog.objects.select_related(
        'investor', 'draft', 'sent_by'
    ).order_by('-sent_at')[:10]
    
    # Recent responses
    recent_responses = ResponseFunding.objects.select_related(
        'investor', 'communication'
    ).order_by('-response_date')[:5]
    
    context = {
        'total_investors': total_investors,
        'total_artifacts': total_artifacts,
        'total_drafts': total_drafts,
        'total_emails_sent': total_emails_sent,
        'emails_7_days': emails_7_days,
        'emails_15_days': emails_15_days,
        'emails_30_days': emails_30_days,
        'emails_older': emails_older,
        'response_data': response_data,
        'recent_communications': recent_communications,
        'recent_responses': recent_responses,
    }
    
    return render(request, 'core/dashboard.html', context)


# ==================== Chatbot API ====================

@login_required
def chatbot_api(request):
    """API endpoint for chatbot interactions."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({
                    'type': 'error',
                    'message': 'Please enter a message.'
                })
            
            # Process message through chatbot service
            chatbot = ChatbotService(user=request.user)
            response = chatbot.process_message(message)
            
            # Clean data for JSON serialization
            if 'data' in response:
                if 'investors' in response['data']:
                    response['data']['investors'] = [
                        {'id': inv.id, 'name': inv.name, 'email': inv.email, 'amount': float(inv.amount)}
                        for inv in response['data']['investors']
                    ]
                if 'artifacts' in response['data']:
                    response['data']['artifacts'] = [
                        {'id': art.id, 'name': art.name, 'type': art.artifact_type}
                        for art in response['data']['artifacts']
                    ]
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'type': 'error',
                'message': 'Invalid request format.'
            })
    
    return JsonResponse({'type': 'error', 'message': 'Method not allowed'}, status=405)


# ==================== Investor Views ====================

@login_required
def investor_list(request):
    """List all investors with search functionality."""
    query = request.GET.get('q', '')
    
    investors = Investor.objects.all()
    
    if query:
        investors = investors.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(labels__icontains=query)
        )
    
    context = {
        'investors': investors,
        'query': query,
    }
    return render(request, 'core/investor_list.html', context)


@login_required
def investor_create(request):
    """Create a new investor."""
    if request.method == 'POST':
        form = InvestorForm(request.POST)
        if form.is_valid():
            investor = form.save(commit=False)
            investor.updated_by = request.user.username
            investor.save()
            messages.success(request, f'Investor "{investor.name}" created successfully!')
            return redirect('investor_list')
    else:
        form = InvestorForm()
    
    return render(request, 'core/investor_form.html', {'form': form, 'title': 'Add New Investor'})


@login_required
def investor_edit(request, pk):
    """Edit an existing investor."""
    investor = get_object_or_404(Investor, pk=pk)
    
    if request.method == 'POST':
        form = InvestorForm(request.POST, instance=investor)
        if form.is_valid():
            investor = form.save(commit=False)
            investor.updated_by = request.user.username
            investor.save()
            messages.success(request, f'Investor "{investor.name}" updated successfully!')
            return redirect('investor_list')
    else:
        form = InvestorForm(instance=investor)
    
    return render(request, 'core/investor_form.html', {'form': form, 'title': 'Edit Investor', 'investor': investor})


@login_required
def investor_detail(request, pk):
    """View investor details with communication history."""
    investor = get_object_or_404(Investor, pk=pk)
    communications = investor.communications.all().order_by('-sent_at')
    responses = investor.funding_responses.all().order_by('-response_date')
    
    context = {
        'investor': investor,
        'communications': communications,
        'responses': responses,
    }
    return render(request, 'core/investor_detail.html', context)


@login_required
def investor_delete(request, pk):
    """Delete an investor."""
    investor = get_object_or_404(Investor, pk=pk)
    
    if request.method == 'POST':
        name = investor.name
        investor.delete()
        messages.success(request, f'Investor "{name}" deleted successfully!')
        return redirect('investor_list')
    
    return render(request, 'core/confirm_delete.html', {'object': investor, 'type': 'investor'})


# ==================== Artifact Views ====================

@login_required
def artifact_list(request):
    """List all artifacts with search functionality."""
    query = request.GET.get('q', '')
    artifact_type = request.GET.get('type', '')
    
    artifacts = Artifact.objects.all()
    
    if query:
        artifacts = artifacts.filter(
            Q(name__icontains=query) |
            Q(artifact_labels__icontains=query) |
            Q(description__icontains=query)
        )
    
    if artifact_type:
        artifacts = artifacts.filter(artifact_type=artifact_type)
    
    context = {
        'artifacts': artifacts,
        'query': query,
        'artifact_type': artifact_type,
        'artifact_types': Artifact.ARTIFACT_TYPES,
    }
    return render(request, 'core/artifact_list.html', context)


@login_required
def artifact_create(request):
    """Create/upload a new artifact."""
    if request.method == 'POST':
        form = ArtifactForm(request.POST, request.FILES)
        if form.is_valid():
            artifact = form.save(commit=False)
            artifact.created_by = request.user
            artifact.save()
            messages.success(request, f'Artifact "{artifact.name}" uploaded successfully!')
            return redirect('artifact_list')
    else:
        form = ArtifactForm()
    
    return render(request, 'core/artifact_form.html', {'form': form, 'title': 'Upload New Artifact'})


@login_required
def artifact_edit(request, pk):
    """Edit an existing artifact."""
    artifact = get_object_or_404(Artifact, pk=pk)
    
    if request.method == 'POST':
        form = ArtifactForm(request.POST, request.FILES, instance=artifact)
        if form.is_valid():
            form.save()
            messages.success(request, f'Artifact "{artifact.name}" updated successfully!')
            return redirect('artifact_list')
    else:
        form = ArtifactForm(instance=artifact)
    
    return render(request, 'core/artifact_form.html', {'form': form, 'title': 'Edit Artifact', 'artifact': artifact})


@login_required
def artifact_delete(request, pk):
    """Delete an artifact."""
    artifact = get_object_or_404(Artifact, pk=pk)
    
    if request.method == 'POST':
        name = artifact.name
        artifact.delete()
        messages.success(request, f'Artifact "{name}" deleted successfully!')
        return redirect('artifact_list')
    
    return render(request, 'core/confirm_delete.html', {'object': artifact, 'type': 'artifact'})


# ==================== Email Draft Views ====================

@login_required
def draft_list(request):
    """List all email drafts."""
    drafts = EmailDraft.objects.all()
    
    context = {
        'drafts': drafts,
    }
    return render(request, 'core/draft_list.html', context)


@login_required
def draft_create(request):
    """Create a new email draft."""
    if request.method == 'POST':
        form = EmailDraftForm(request.POST)
        if form.is_valid():
            draft = form.save(commit=False)
            draft.created_by = request.user
            draft.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Draft "{draft.name}" created successfully!')
            return redirect('draft_list')
    else:
        form = EmailDraftForm()
    
    return render(request, 'core/draft_form.html', {'form': form, 'title': 'Create Email Draft'})


@login_required
def draft_edit(request, pk):
    """Edit an existing email draft."""
    draft = get_object_or_404(EmailDraft, pk=pk)
    
    if request.method == 'POST':
        form = EmailDraftForm(request.POST, instance=draft)
        if form.is_valid():
            form.save()
            messages.success(request, f'Draft "{draft.name}" updated successfully!')
            return redirect('draft_list')
    else:
        form = EmailDraftForm(instance=draft)
    
    return render(request, 'core/draft_form.html', {'form': form, 'title': 'Edit Email Draft', 'draft': draft})


@login_required
def draft_delete(request, pk):
    """Delete an email draft."""
    draft = get_object_or_404(EmailDraft, pk=pk)
    
    if request.method == 'POST':
        name = draft.name
        draft.delete()
        messages.success(request, f'Draft "{name}" deleted successfully!')
        return redirect('draft_list')
    
    return render(request, 'core/confirm_delete.html', {'object': draft, 'type': 'draft'})


# ==================== Response/Funding Views ====================

@login_required
def response_list(request):
    """List all investor responses."""
    responses = ResponseFunding.objects.select_related('investor', 'communication').all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        responses = responses.filter(response_status=status_filter)
    
    context = {
        'responses': responses,
        'status_filter': status_filter,
        'status_choices': ResponseFunding.RESPONSE_STATUS,
    }
    return render(request, 'core/response_list.html', context)


@login_required
def response_create(request):
    """Record a new investor response."""
    if request.method == 'POST':
        form = ResponseFundingForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.created_by = request.user
            response.save()
            messages.success(request, 'Response recorded successfully!')
            return redirect('response_list')
    else:
        form = ResponseFundingForm()
    
    return render(request, 'core/response_form.html', {'form': form, 'title': 'Record Investor Response'})


@login_required
def response_edit(request, pk):
    """Edit an investor response."""
    response_obj = get_object_or_404(ResponseFunding, pk=pk)
    
    if request.method == 'POST':
        form = ResponseFundingForm(request.POST, instance=response_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Response updated successfully!')
            return redirect('response_list')
    else:
        form = ResponseFundingForm(instance=response_obj)
    
    return render(request, 'core/response_form.html', {'form': form, 'title': 'Edit Response', 'response': response_obj})


@login_required
def response_delete(request, pk):
    """Delete a response record."""
    response_obj = get_object_or_404(ResponseFunding, pk=pk)
    
    if request.method == 'POST':
        response_obj.delete()
        messages.success(request, 'Response deleted successfully!')
        return redirect('response_list')
    
    return render(request, 'core/confirm_delete.html', {'object': response_obj, 'type': 'response'})


# ==================== Communication Log Views ====================

@login_required
def communication_list(request):
    """List all communication logs."""
    communications = CommunicationLog.objects.select_related(
        'investor', 'draft', 'sent_by'
    ).all()
    
    context = {
        'communications': communications,
    }
    return render(request, 'core/communication_list.html', context)
