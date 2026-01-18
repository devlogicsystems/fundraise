from django.db import models
from django.contrib.auth.models import User


class Investor(models.Model):
    """
    Investor/Potential Investor data model.
    Stores all information about investors including contact details and funding amounts.
    """
    name = models.CharField(max_length=255, help_text="Investor name")
    email = models.EmailField(unique=True, help_text="Investor email address")
    labels = models.CharField(
        max_length=500, 
        blank=True, 
        help_text="Comma-separated labels for search (e.g., 'VC, Tech, Series-A')"
    )
    address = models.TextField(blank=True, help_text="Investor address")
    details = models.TextField(blank=True, help_text="Additional details about the investor")
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        help_text="Amount in Rs."
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_on = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, blank=True, help_text="Username who last updated")

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.name} ({self.email})"

    def get_labels_list(self):
        """Return labels as a list."""
        if self.labels:
            return [label.strip() for label in self.labels.split(',')]
        return []


class Artifact(models.Model):
    """
    Artifact Inventory model.
    Stores images, videos, and presentations for sharing with investors.
    """
    ARTIFACT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('presentation', 'Presentation'),
    ]

    artifact_type = models.CharField(
        max_length=20, 
        choices=ARTIFACT_TYPES, 
        help_text="Type of artifact"
    )
    artifact_labels = models.CharField(
        max_length=500, 
        blank=True, 
        help_text="Comma-separated labels for keyword search"
    )
    file = models.FileField(upload_to='artifacts/', help_text="Upload file")
    name = models.CharField(max_length=255, help_text="Artifact name/title")
    description = models.TextField(blank=True, help_text="Description of the artifact")
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='artifacts'
    )

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.name} ({self.artifact_type})"

    def get_labels_list(self):
        """Return labels as a list."""
        if self.artifact_labels:
            return [label.strip() for label in self.artifact_labels.split(',')]
        return []


class EmailDraft(models.Model):
    """
    Email Draft model.
    Stores reusable email templates with attached artifacts.
    """
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Unique draft name (e.g., 'pitchdeck', 'intro_email')"
    )
    subject = models.CharField(max_length=255, help_text="Email subject line")
    body = models.TextField(help_text="Email body content (supports HTML)")
    artifacts = models.ManyToManyField(
        Artifact, 
        blank=True, 
        related_name='email_drafts',
        help_text="Select artifacts to attach to this email"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='email_drafts'
    )

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.name


class CommunicationLog(models.Model):
    """
    Communication Log model.
    Tracks all emails sent to investors.
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    investor = models.ForeignKey(
        Investor, 
        on_delete=models.CASCADE, 
        related_name='communications'
    )
    draft = models.ForeignKey(
        EmailDraft, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='communications'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_communications'
    )
    notes = models.TextField(blank=True, help_text="Additional notes about this communication")

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.investor.email} on {self.sent_at.strftime('%Y-%m-%d %H:%M')}"


class ResponseFunding(models.Model):
    """
    Response/Funding model.
    Tracks investor responses to communications with funding outcomes.
    """
    RESPONSE_STATUS = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('pending', 'Pending'),
    ]

    communication = models.ForeignKey(
        CommunicationLog, 
        on_delete=models.CASCADE, 
        related_name='responses'
    )
    investor = models.ForeignKey(
        Investor, 
        on_delete=models.CASCADE, 
        related_name='funding_responses'
    )
    response_status = models.CharField(
        max_length=10, 
        choices=RESPONSE_STATUS, 
        default='pending',
        help_text="Response status from investor"
    )
    amount_offered = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        help_text="Amount offered by investor (Rs.)"
    )
    notes = models.TextField(blank=True, help_text="Response notes/comments")
    response_date = models.DateTimeField(help_text="When response was received")
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_responses'
    )

    class Meta:
        ordering = ['-response_date']
        verbose_name = "Response/Funding"
        verbose_name_plural = "Responses/Funding"

    def __str__(self):
        return f"{self.investor.name} - {self.response_status} ({self.response_date.strftime('%Y-%m-%d')})"
