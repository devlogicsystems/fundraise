from django.contrib import admin
from .models import Investor, Artifact, EmailDraft, CommunicationLog, ResponseFunding


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'amount', 'created_date', 'last_updated_on']
    list_filter = ['created_date']
    search_fields = ['name', 'email', 'labels']
    readonly_fields = ['created_date', 'last_updated_on']


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'artifact_type', 'created_date', 'created_by']
    list_filter = ['artifact_type', 'created_date']
    search_fields = ['name', 'artifact_labels']
    readonly_fields = ['created_date']


@admin.register(EmailDraft)
class EmailDraftAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'subject', 'created_date', 'created_by']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_date', 'last_updated_on']
    filter_horizontal = ['artifacts']


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'investor', 'draft', 'status', 'sent_at', 'sent_by']
    list_filter = ['status', 'sent_at']
    search_fields = ['investor__name', 'investor__email']
    readonly_fields = ['sent_at']


@admin.register(ResponseFunding)
class ResponseFundingAdmin(admin.ModelAdmin):
    list_display = ['id', 'investor', 'response_status', 'amount_offered', 'response_date', 'created_by']
    list_filter = ['response_status', 'response_date']
    search_fields = ['investor__name', 'notes']
    readonly_fields = ['created_date']
