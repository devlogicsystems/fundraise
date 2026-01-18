"""
Chatbot service for processing user commands.
Handles email sending commands, search queries, and generic AI responses using Gemini.
"""
import re
from django.conf import settings
from .models import Investor, Artifact, EmailDraft, CommunicationLog

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class ChatbotService:
    """Service for processing chatbot commands and generating responses."""
    
    # Regex patterns for command parsing
    SEND_EMAIL_PATTERN = re.compile(
        r'send\s+email\s+to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+(?:the\s+)?draft\s+(?:of\s+)?["\']?(\w+)["\']?',
        re.IGNORECASE
    )
    
    SEARCH_PATTERN = re.compile(
        r'show\s+(?:me\s+)?data\s+for\s*[-:]?\s*(.+)',
        re.IGNORECASE
    )
    
    def __init__(self, user=None):
        self.user = user
        self.gemini_model = None
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini AI model."""
        if GEMINI_AVAILABLE and hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY != 'your-gemini-api-key-here':
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
    
    def process_message(self, message):
        """
        Process user message and return appropriate response.
        
        Returns:
            dict: Response with 'type', 'message', and optionally 'data'
        """
        message = message.strip()
        
        # Check for send email command
        email_match = self.SEND_EMAIL_PATTERN.search(message)
        if email_match:
            return self._handle_send_email(email_match.group(1), email_match.group(2))
        
        # Check for search command
        search_match = self.SEARCH_PATTERN.search(message)
        if search_match:
            return self._handle_search(search_match.group(1))
        
        # Handle as generic query with Gemini
        return self._handle_generic_query(message)
    
    def _handle_send_email(self, email_address, draft_name):
        """Handle send email command."""
        from .email_service import EmailService
        
        # Find the draft
        try:
            draft = EmailDraft.objects.get(name__iexact=draft_name)
        except EmailDraft.DoesNotExist:
            # List available drafts
            available_drafts = EmailDraft.objects.values_list('name', flat=True)
            drafts_list = ", ".join(available_drafts) if available_drafts else "No drafts available"
            return {
                'type': 'error',
                'message': f"❌ Draft '{draft_name}' not found. Available drafts: {drafts_list}"
            }
        
        # Get or create investor
        investor, created = Investor.objects.get_or_create(
            email=email_address,
            defaults={
                'name': email_address.split('@')[0],
                'updated_by': self.user.username if self.user else 'system'
            }
        )
        
        investor_status = "Created new investor" if created else "Found existing investor"
        
        # Send email
        email_service = EmailService()
        success, message = email_service.send_draft_email(
            investor=investor,
            draft=draft,
            user=self.user
        )
        
        if success:
            return {
                'type': 'success',
                'message': f"✅ Email sent successfully!\n\n📧 To: {email_address}\n📋 Draft: {draft_name}\n👤 {investor_status}: {investor.name}",
                'data': {
                    'investor': investor,
                    'draft': draft
                }
            }
        else:
            return {
                'type': 'error',
                'message': f"❌ Failed to send email: {message}"
            }
    
    def _handle_search(self, query_string):
        """Handle search command."""
        # Extract keywords from query (handle quoted and unquoted)
        keywords = re.findall(r"['\"]([^'\"]+)['\"]|(\w+)", query_string)
        keywords = [k[0] or k[1] for k in keywords if k[0] or k[1]]
        keywords = [k.strip() for k in keywords if k.strip() and k.lower() not in ['and', 'or', 'for', 'the']]
        
        if not keywords:
            return {
                'type': 'error',
                'message': "❌ Please provide keywords to search for."
            }
        
        # Search investors
        investors = []
        for keyword in keywords:
            matching_investors = Investor.objects.filter(
                name__icontains=keyword
            ) | Investor.objects.filter(
                email__icontains=keyword
            ) | Investor.objects.filter(
                labels__icontains=keyword
            )
            investors.extend(matching_investors)
        
        # Remove duplicates
        investors = list({inv.id: inv for inv in investors}.values())
        
        # Search artifacts
        artifacts = []
        for keyword in keywords:
            matching_artifacts = Artifact.objects.filter(
                name__icontains=keyword
            ) | Artifact.objects.filter(
                artifact_labels__icontains=keyword
            ) | Artifact.objects.filter(
                description__icontains=keyword
            )
            artifacts.extend(matching_artifacts)
        
        # Remove duplicates
        artifacts = list({art.id: art for art in artifacts}.values())
        
        # Build response
        response_parts = [f"🔍 Search results for: {', '.join(keywords)}\n"]
        
        if investors:
            response_parts.append(f"\n👥 **Investors ({len(investors)}):**")
            for inv in investors[:10]:  # Limit to 10
                response_parts.append(f"  • {inv.name} ({inv.email}) - ₹{inv.amount:,.2f}")
        else:
            response_parts.append("\n👥 No investors found.")
        
        if artifacts:
            response_parts.append(f"\n📎 **Artifacts ({len(artifacts)}):**")
            for art in artifacts[:10]:  # Limit to 10
                response_parts.append(f"  • {art.name} ({art.artifact_type})")
        else:
            response_parts.append("\n📎 No artifacts found.")
        
        return {
            'type': 'search_results',
            'message': "\n".join(response_parts),
            'data': {
                'investors': investors,
                'artifacts': artifacts,
                'keywords': keywords
            }
        }
    
    def _handle_generic_query(self, message):
        """Handle generic queries using Gemini AI."""
        if not self.gemini_model:
            return self._fallback_response(message)
        
        try:
            # Get context data
            investor_count = Investor.objects.count()
            artifact_count = Artifact.objects.count()
            draft_count = EmailDraft.objects.count()
            recent_emails = CommunicationLog.objects.count()
            
            # Build context prompt
            context = f"""You are an AI assistant for a startup fundraising application. 
Here's the current data context:
- Total Investors: {investor_count}
- Total Artifacts: {artifact_count}  
- Email Drafts: {draft_count}
- Emails Sent: {recent_emails}

Available commands the user can use:
1. "Send email to <email> the draft of <draft_name>" - Sends an email draft to an investor
2. "Show me data for - '<keyword1>', '<keyword2>'" - Searches investors and artifacts

User's question: {message}

Provide a helpful, concise response. If they're asking about functionality, guide them on how to use the app.
Keep responses brief and friendly."""

            response = self.gemini_model.generate_content(context)
            
            return {
                'type': 'ai_response',
                'message': f"🤖 {response.text}"
            }
        except Exception as e:
            return self._fallback_response(message)
    
    def _fallback_response(self, message):
        """Provide fallback response when Gemini is unavailable."""
        help_text = """👋 I'm your fundraising assistant! Here's what I can do:

📧 **Send Email:**
   `Send email to investor@email.com the draft of pitchdeck`

🔍 **Search Data:**
   `Show me data for - 'keyword1', 'keyword2'`

📊 **Quick Stats:**
   - Investors: {investor_count}
   - Artifacts: {artifact_count}
   - Email Drafts: {draft_count}

💡 Tip: Configure your Gemini API key for AI-powered responses!"""
        
        investor_count = Investor.objects.count()
        artifact_count = Artifact.objects.count()
        draft_count = EmailDraft.objects.count()
        
        return {
            'type': 'help',
            'message': help_text.format(
                investor_count=investor_count,
                artifact_count=artifact_count,
                draft_count=draft_count
            )
        }
