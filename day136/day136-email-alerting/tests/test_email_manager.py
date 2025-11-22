import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.email_service.email_manager import EmailManager, EmailConfig, EmailMessage

@pytest.fixture
def email_config():
    return EmailConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        username="test@example.com",
        password="test_password",
        from_email="noreply@test.com",
        from_name="Test System"
    )

@pytest.fixture
def email_manager(email_config):
    with patch('redis.Redis'):
        manager = EmailManager(email_config)
        manager.redis_client = Mock()
        return manager

def test_email_manager_initialization(email_manager):
    """Test EmailManager initializes correctly"""
    assert email_manager.config.smtp_host == "smtp.test.com"
    assert email_manager.delivery_stats['sent'] == 0
    assert email_manager.delivery_stats['failed'] == 0

@pytest.mark.asyncio
async def test_send_email_success(email_manager):
    """Test successful email sending"""
    message = EmailMessage(
        to_emails=["test@example.com"],
        subject="Test Email",
        html_body="<h1>Test</h1>",
        priority="normal"
    )
    
    with patch('aiosmtplib.SMTP') as mock_smtp:
        mock_server = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_server
        
        result = await email_manager.send_email(message)
        
        assert result["status"] == "sent"
        assert "delivery_id" in result
        assert email_manager.delivery_stats['sent'] == 1

def test_render_template(email_manager):
    """Test template rendering"""
    with patch.object(email_manager.template_env, 'get_template') as mock_get_template:
        mock_template = Mock()
        mock_template.render.return_value = "<h1>Hello Test</h1>"
        mock_get_template.return_value = mock_template
        
        result = email_manager.render_template('test.html', {'name': 'Test'})
        
        assert result == "<h1>Hello Test</h1>"
        mock_template.render.assert_called_once_with(name='Test')

def test_get_delivery_stats(email_manager):
    """Test delivery statistics calculation"""
    email_manager.delivery_stats['sent'] = 10
    email_manager.delivery_stats['failed'] = 2
    
    stats = email_manager.get_delivery_stats()
    
    assert stats['sent'] == 10
    assert stats['failed'] == 2
    assert stats['success_rate'] == pytest.approx(83.33, rel=1e-2)
