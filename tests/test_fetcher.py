import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the classes we want to test
from fetch_secure_session_improved import (
    Config, SecureSessionManager, MessageParser, 
    DataManager, DataProcessor, TelegramFetcher
)

class TestConfig:
    """Test configuration management"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.dict(os.environ, {
            'API_ID': '12345',
            'API_HASH': 'abcdef1234567890abcdef1234567890'
        }):
            config = Config()
            assert config.validate() is True
    
    def test_config_validation_missing_credentials(self):
        """Test configuration validation with missing credentials"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.validate() is False
    
    def test_config_validation_invalid_api_id(self):
        """Test configuration validation with invalid API ID"""
        with patch.dict(os.environ, {
            'API_ID': 'invalid',
            'API_HASH': 'abcdef1234567890abcdef1234567890'
        }):
            config = Config()
            assert config.validate() is False

class TestSecureSessionManager:
    """Test secure session management"""
    
    def test_create_session_file_success(self):
        """Test successful session file creation"""
        session_data = b"test_session_data"
        session_base64 = "dGVzdF9zZXNzaW9uX2RhdGE="  # base64 of test_session_data
        
        with patch('os.getenv', return_value=session_base64):
            manager = SecureSessionManager(session_base64)
            
            with tempfile.TemporaryDirectory():
                result = manager.create_session_file()
                assert result is True
                assert os.path.exists('telegram_session.session')
    
    def test_create_session_file_missing_data(self):
        """Test session file creation with missing data"""
        manager = SecureSessionManager(None)
        result = manager.create_session_file()
        assert result is False
    
    def test_cleanup_session_file(self):
        """Test session file cleanup"""
        session_base64 = "dGVzdF9zZXNzaW9uX2RhdGE="
        manager = SecureSessionManager(session_base64)
        
        with tempfile.TemporaryDirectory():
            # Create a dummy session file
            with open('telegram_session.session', 'w') as f:
                f.write('test')
            
            manager.cleanup_session_file()
            assert not os.path.exists('telegram_session.session')

class TestMessageParser:
    """Test message parsing functionality"""
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        text = "**🔹 ****t.me/breachdetector**** 🔹** Test message with watermarks"
        cleaned = MessageParser.clean_text(text)
        assert "t.me/breachdetector" not in cleaned
        assert "🔹" not in cleaned
        assert "Test message with watermarks" in cleaned
    
    def test_parse_message_content_json(self):
        """Test parsing JSON message content"""
        json_content = '{"Source": "test.com", "Content": "Test breach", "Type": "Data leak"}'
        result = MessageParser.parse_message_content(json_content)
        assert result["Source"] == "test.com"
        assert result["Content"] == "Test breach"
        assert result["Type"] == "Data leak"
    
    def test_parse_message_content_plain_text(self):
        """Test parsing plain text message content"""
        text_content = "Simple breach message"
        result = MessageParser.parse_message_content(text_content)
        assert result["Content"] == "Simple breach message"
        assert result["Source"] == "Unknown"
        assert result["Type"] == "Data leak"

class TestDataProcessor:
    """Test data processing functionality"""
    
    def test_deduplicate_messages(self):
        """Test message deduplication"""
        existing = [
            {"Content": "Test breach 1", "Source": "test.com"},
            {"Content": "Test breach 2", "Source": "test.com"}
        ]
        new = [
            {"Content": "Test breach 2", "Source": "test.com"},  # Duplicate
            {"Content": "Test breach 3", "Source": "test.com"}   # New
        ]
        
        result = DataProcessor.deduplicate_messages(existing, new)
        assert len(result) == 3  # Should have 3 unique messages
        contents = [msg["Content"] for msg in result]
        assert "Test breach 1" in contents
        assert "Test breach 2" in contents
        assert "Test breach 3" in contents
    
    def test_validate_message_structure_valid(self):
        """Test valid message structure validation"""
        message = {"Content": "Test breach", "Source": "test.com", "Type": "Data leak"}
        assert DataProcessor.validate_message_structure(message) is True
    
    def test_validate_message_structure_invalid(self):
        """Test invalid message structure validation"""
        message = {"Source": "test.com", "Type": "Data leak"}  # Missing Content
        assert DataProcessor.validate_message_structure(message) is False
        
        message = {"Content": "", "Source": "test.com"}  # Empty Content
        assert DataProcessor.validate_message_structure(message) is False

@pytest.mark.asyncio
class TestDataManager:
    """Test data management functionality"""
    
    async def test_load_existing_data_success(self):
        """Test successful loading of existing data"""
        test_data = [{"Content": "Test breach", "Source": "test.com"}]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create test data file
            with open('data.json', 'w') as f:
                json.dump(test_data, f)
            
            config = Config()
            manager = DataManager(config)
            result = await manager.load_existing_data()
            
            assert result == test_data
    
    async def test_load_existing_data_file_not_found(self):
        """Test loading when data file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            config = Config()
            manager = DataManager(config)
            result = await manager.load_existing_data()
            
            assert result == []
    
    async def test_save_data_success(self):
        """Test successful data saving"""
        test_data = [{"Content": "Test breach", "Source": "test.com"}]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            config = Config()
            manager = DataManager(config)
            await manager.save_data(test_data, 1)
            
            # Verify file was created
            assert os.path.exists('data.json')
            
            # Verify content
            with open('data.json', 'r') as f:
                saved_data = json.load(f)
            assert saved_data == test_data

@pytest.mark.asyncio
class TestTelegramFetcher:
    """Test Telegram fetcher functionality"""
    
    @patch('telethon.TelegramClient')
    async def test_fetch_messages_success(self, mock_client):
        """Test successful message fetching"""
        # Mock client setup
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        # Mock message
        mock_message = Mock()
        mock_message.text = '{"Content": "Test breach", "Source": "test.com"}'
        mock_message.id = 123
        mock_message.date = datetime.now()
        
        mock_client_instance.iter_messages.return_value = [mock_message]
        mock_client_instance.get_entity.return_value = Mock()
        mock_client_instance.is_user_authorized.return_value = True
        
        # Setup config
        with patch.dict(os.environ, {
            'API_ID': '12345',
            'API_HASH': 'abcdef1234567890abcdef1234567890',
            'GITHUB_ACTIONS': 'true'
        }):
            config = Config()
            fetcher = TelegramFetcher(config)
            
            # Mock session creation
            with patch.object(fetcher.session_manager, 'create_session_file', return_value=True):
                result = await fetcher._fetch_messages()
                
                assert len(result) == 1
                assert result[0]["Content"] == "Test breach"
                assert result[0]["Source"] == "test.com"
    
    @patch('telethon.TelegramClient')
    async def test_fetch_messages_rate_limit(self, mock_client):
        """Test handling of rate limiting"""
        from telethon.errors import FloodWaitError
        
        mock_client_instance = AsyncMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.get_entity.side_effect = FloodWaitError(60)
        
        with patch.dict(os.environ, {
            'API_ID': '12345',
            'API_HASH': 'abcdef1234567890abcdef1234567890'
        }):
            config = Config()
            fetcher = TelegramFetcher(config)
            
            result = await fetcher.fetch_messages_with_retry()
            assert result == []

# Integration tests
@pytest.mark.asyncio
class TestIntegration:
    """Integration tests"""
    
    async def test_full_workflow(self):
        """Test the complete workflow"""
        # This would test the entire pipeline from config to data saving
        # Implementation would depend on mocking external dependencies
        pass

# Performance tests
class TestPerformance:
    """Performance tests"""
    
    def test_large_data_processing(self):
        """Test processing of large datasets"""
        # Create large dataset
        large_dataset = [
            {"Content": f"Test breach {i}", "Source": "test.com"}
            for i in range(10000)
        ]
        
        # Test deduplication performance
        import time
        start_time = time.time()
        result = DataProcessor.deduplicate_messages(large_dataset, [])
        end_time = time.time()
        
        assert len(result) == 10000
        assert end_time - start_time < 5.0  # Should complete within 5 seconds

if __name__ == "__main__":
    pytest.main([__file__]) 