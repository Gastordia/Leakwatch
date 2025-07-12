#!/usr/bin/env python3
"""
Improved Secure Telegram Fetcher with Enhanced Security and Features
Uses GitHub secrets to handle session files securely with better error handling
"""

import os
import json
import asyncio
import base64
import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError, AuthKeyUnregisteredError
from telethon.tl.types import Message
import aiofiles
import yaml

# Security constants
SECURE_FILE_PERMISSIONS = 0o600
MAX_CONTENT_LENGTH = 2000
MAX_SOURCE_LENGTH = 500
ALLOWED_BREACH_TYPES = ["Data leak", "Security breach", "Privacy violation", "Ransomware", "Malware", "Phishing", "DDoS", "Other"]

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BreachEntry:
    """Structured breach data entry"""
    source: str
    content: str
    author: str
    detection_date: str
    breach_type: str
    message_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    hash_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate hash ID for deduplication and validate data"""
        if not self.hash_id:
            content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
            self.hash_id = f"{self.source}_{content_hash}"
        
        # Validate and sanitize data
        self._validate_and_sanitize()
    
    def _validate_and_sanitize(self):
        """Validate and sanitize breach entry data"""
        # Sanitize source
        if len(self.source) > MAX_SOURCE_LENGTH:
            self.source = self.source[:MAX_SOURCE_LENGTH]
        
        # Sanitize content
        if len(self.content) > MAX_CONTENT_LENGTH:
            self.content = self.content[:MAX_CONTENT_LENGTH]
        
        # Validate breach type
        if self.breach_type not in ALLOWED_BREACH_TYPES:
            self.breach_type = "Other"
        
        # Sanitize author (remove potentially malicious characters)
        self.author = re.sub(r'[<>"\']', '', self.author)[:100]

class Config:
    """Configuration management with validation"""
    
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.session_base64 = os.getenv('TELEGRAM_SESSION_BASE64')
        self.channel = os.getenv('CHANNEL', 'breachdetector')
        self.message_limit = int(os.getenv('MESSAGE_LIMIT', '5000'))
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '50')) * 1024 * 1024  # 50MB default
        self.backup_enabled = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY_SECONDS', '60'))
        
    def validate(self) -> bool:
        """Validate configuration with enhanced security checks"""
        if not self.api_id or not self.api_hash:
            logger.error("API_ID and API_HASH environment variables are required")
            return False
        
        if not self.api_id.isdigit():
            logger.error("API_ID must be a numeric value")
            return False
            
        if len(self.api_hash) != 32:
            logger.error("API_HASH must be 32 characters long")
            return False
        
        # Validate channel name format
        if not re.match(r'^[a-zA-Z0-9_]+$', self.channel):
            logger.error("Channel name contains invalid characters")
            return False
            
        return True

class SecureSessionManager:
    """Enhanced session management with security features"""
    
    def __init__(self, session_base64: str):
        self.session_base64 = session_base64
        self.session_file = 'telegram_session.session'
        self.session_checksum = None
        
    def create_session_file(self) -> bool:
        """Create session file with integrity checking and secure permissions"""
        if not self.session_base64:
            logger.error("TELEGRAM_SESSION_BASE64 environment variable is required")
            return False
        
        try:
            # Validate base64 format
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', self.session_base64):
                logger.error("Invalid base64 format for session data")
                return False
            
            # Decode base64 session data
            session_data = base64.b64decode(self.session_base64)
            
            # Calculate checksum for integrity
            self.session_checksum = hashlib.sha256(session_data).hexdigest()
            
            # Write to session file with secure permissions
            with open(self.session_file, 'wb') as f:
                f.write(session_data)
            
            # Set secure file permissions
            os.chmod(self.session_file, SECURE_FILE_PERMISSIONS)
            
            logger.info(f"✅ Session file created with secure permissions (checksum: {self.session_checksum[:16]}...)")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session file: {e}")
            return False
    
    def cleanup_session_file(self):
        """Remove session file and clear sensitive data"""
        try:
            if os.path.exists(self.session_file):
                # Securely overwrite file before deletion
                with open(self.session_file, 'wb') as f:
                    f.write(b'\x00' * os.path.getsize(self.session_file))
                os.remove(self.session_file)
                logger.info("✅ Session file securely cleaned up")
                
            # Clear checksum
            self.session_checksum = None
            
        except Exception as e:
            logger.error(f"Error cleaning up session file: {e}")

class MessageParser:
    """Enhanced message parsing with better error handling and security"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean message text from watermarks and formatting with security checks"""
        if not isinstance(text, str):
            return ""
        
        # Remove watermarks
        watermarks = [
            '**🔹 ****t.me/breachdetector**** 🔹**',
            't.me/breachdetector',
            '**🔹',
            '🔹**'
        ]
        
        clean_text = text
        for watermark in watermarks:
            clean_text = clean_text.replace(watermark, '')
        
        # Handle escaped characters
        clean_text = clean_text.replace('\\n', ' ').replace('\\"', '"')
        
        # Remove potentially dangerous characters
        clean_text = re.sub(r'[<>"\']', '', clean_text)
        
        return clean_text.strip()
    
    @staticmethod
    def parse_message_content(message_text: str) -> Optional[Dict[str, Any]]:
        """Parse message content with enhanced error handling and validation"""
        try:
            if not isinstance(message_text, str):
                return None
                
            clean_text = MessageParser.clean_text(message_text)
            
            # Validate content length
            if len(clean_text) > MAX_CONTENT_LENGTH:
                clean_text = clean_text[:MAX_CONTENT_LENGTH]
            
            # Try to parse as JSON
            for attempt in range(2):
                try:
                    parsed = json.loads(clean_text)
                    if isinstance(parsed, str):
                        clean_text = parsed
                        continue
                    
                    # Validate parsed JSON structure
                    if isinstance(parsed, dict):
                        # Ensure required fields exist
                        if 'Content' not in parsed:
                            parsed['Content'] = clean_text
                        if 'Source' not in parsed:
                            parsed['Source'] = 'Unknown'
                        if 'Type' not in parsed:
                            parsed['Type'] = 'Data leak'
                        
                        # Validate field types and lengths
                        for key, value in parsed.items():
                            if isinstance(value, str):
                                if key == 'Content' and len(value) > MAX_CONTENT_LENGTH:
                                    parsed[key] = value[:MAX_CONTENT_LENGTH]
                                elif key == 'Source' and len(value) > MAX_SOURCE_LENGTH:
                                    parsed[key] = value[:MAX_SOURCE_LENGTH]
                    
                    return parsed
                except json.JSONDecodeError:
                    break
            
            # If JSON parsing fails, return as plain text
            return {"Content": clean_text, "Source": "Unknown", "Type": "Data leak"}
            
        except Exception as e:
            logger.warning(f"Failed to parse message content: {e}")
            return None

class DataManager:
    """Enhanced data management with backup and validation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_file = 'data.json'
        self.backup_file = 'data_backup.json'
        
    async def load_existing_data(self) -> List[Dict[str, Any]]:
        """Load existing data with error handling"""
        try:
            async with aiofiles.open(self.data_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                logger.info(f"Loaded {len(data)} existing messages")
                return data
        except FileNotFoundError:
            logger.info("No existing data.json found, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            return []
    
    async def save_data(self, messages: List[Dict[str, Any]], new_count: int):
        """Save data with backup and validation"""
        try:
            # Create backup if enabled
            if self.config.backup_enabled:
                await self._create_backup()
            
            # Validate file size
            if len(messages) > 10000:  # Prevent excessive growth
                messages = messages[:10000]
                logger.warning("Truncated to 10,000 messages to prevent excessive file size")
            
            # Save to file
            async with aiofiles.open(self.data_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(messages, indent=2, ensure_ascii=False))
            
            logger.info(f"Saved {len(messages)} total messages (added {new_count} new)")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    async def _create_backup(self):
        """Create backup of current data"""
        try:
            if os.path.exists(self.data_file):
                async with aiofiles.open(self.data_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                async with aiofiles.open(self.backup_file, 'w', encoding='utf-8') as f:
                    await f.write(content)
                
                logger.info("✅ Backup created")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")

class TelegramFetcher:
    """Enhanced Telegram message fetcher with retry logic and security"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SecureSessionManager(config.session_base64)
        self.data_manager = DataManager(config)
        self.parser = MessageParser()
        
    async def fetch_messages_with_retry(self) -> List[Dict[str, Any]]:
        """Fetch messages with retry logic and enhanced error handling"""
        for attempt in range(self.config.retry_attempts):
            try:
                return await self._fetch_messages()
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    logger.error("All retry attempts failed")
                    return []
        
        return []
    
    async def _fetch_messages(self) -> List[Dict[str, Any]]:
        """Fetch messages from Telegram channel with enhanced security"""
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        if is_github_actions and not self.config.session_base64:
            logger.error("TELEGRAM_SESSION_BASE64 is required for GitHub Actions")
            return []
        
        try:
            # Create session file if in GitHub Actions
            if is_github_actions:
                if not self.session_manager.create_session_file():
                    return []
            
            # Create client
            client = TelegramClient('telegram_session', self.config.api_id, self.config.api_hash)
            
            logger.info(f"Connecting to Telegram...")
            
            if is_github_actions:
                logger.info("Running in GitHub Actions - using session file...")
                await client.connect()
                
                if not await client.is_user_authorized():
                    logger.error("Session file is invalid or expired")
                    return []
            else:
                await client.start()
            
            logger.info(f"Fetching messages from @{self.config.channel}...")
            
            # Get channel entity
            try:
                channel = await client.get_entity(f"@{self.config.channel}")
            except Exception as e:
                logger.error(f"Could not find channel @{self.config.channel}: {e}")
                return []
            
            # Fetch messages with quality filtering
            all_messages = []
            async for message in client.iter_messages(channel, limit=self.config.message_limit):
                if message.text:
                    parsed_content = self.parser.parse_message_content(message.text)
                    if parsed_content and DataProcessor.validate_message_structure(parsed_content):
                        # Add message metadata
                        parsed_content['message_id'] = message.id
                        parsed_content['timestamp'] = message.date.isoformat()
                        all_messages.append(parsed_content)
            
            logger.info(f"Fetched {len(all_messages)} valid messages")
            await client.disconnect()
            return all_messages
            
        except SessionPasswordNeededError:
            logger.error("Two-factor authentication is enabled. Cannot automate this.")
            return []
        except AuthKeyUnregisteredError:
            logger.error("Session is invalid. Please regenerate session file.")
            return []
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
        finally:
            if is_github_actions:
                self.session_manager.cleanup_session_file()

class DataProcessor:
    """Enhanced data processing with deduplication and validation"""
    
    # Keywords that indicate actual breaches vs spam/ads
    BREACH_INDICATORS = [
        'leak', 'breach', 'hack', 'compromise', 'exposed', 'stolen', 'database',
        'credentials', 'password', 'email', 'personal data', 'user data',
        'customer data', 'financial data', 'credit card', 'ssn', 'social security'
    ]
    
    SPAM_INDICATORS = [
        'buy', 'sell', 'offer', 'discount', 'promotion', 'service', 'tool',
        'software', 'review', 'rating', 'backlink', 'seo', 'marketing',
        'advertisement', 'sponsored', 'deal', 'sale', 'free trial'
    ]
    
    @staticmethod
    def is_legitimate_breach(content: str) -> bool:
        """Check if content represents a legitimate breach vs spam/ad"""
        if not content:
            return False
            
        content_lower = content.lower()
        
        # Check for spam indicators
        spam_score = sum(1 for indicator in DataProcessor.SPAM_INDICATORS 
                        if indicator in content_lower)
        
        # Check for breach indicators
        breach_score = sum(1 for indicator in DataProcessor.BREACH_INDICATORS 
                          if indicator in content_lower)
        
        # Content is legitimate if it has more breach indicators than spam
        return breach_score > spam_score and breach_score > 0
    
    @staticmethod
    def deduplicate_messages(existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate messages using content hash with quality filtering"""
        seen_hashes = set()
        unique_messages = []
        
        # Process existing messages
        for msg in existing:
            content = msg.get('Content', '').strip()
            if content and DataProcessor.is_legitimate_breach(content):
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique_messages.append(msg)
        
        # Process new messages
        for msg in new:
            content = msg.get('Content', '').strip()
            if content and DataProcessor.is_legitimate_breach(content):
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique_messages.append(msg)
        
        logger.info(f"Filtered to {len(unique_messages)} legitimate breach messages")
        return unique_messages
    
    @staticmethod
    def validate_message_structure(message: Dict[str, Any]) -> bool:
        """Validate message structure with enhanced checks"""
        required_fields = ['Content']
        
        # Check required fields exist
        if not all(field in message for field in required_fields):
            return False
        
        # Check content is not empty
        content = message.get('Content', '').strip()
        if not content:
            return False
        
        # Check content length
        if len(content) > MAX_CONTENT_LENGTH:
            return False
        
        # Check if it's a legitimate breach
        return DataProcessor.is_legitimate_breach(content)

async def main():
    """Main function with enhanced error handling"""
    logger.info("Starting enhanced Telegram channel fetch...")
    
    # Initialize configuration
    config = Config()
    if not config.validate():
        return
    
    # Initialize components
    fetcher = TelegramFetcher(config)
    processor = DataProcessor()
    
    try:
        # Fetch new messages
        new_messages = await fetcher.fetch_messages_with_retry()
        
        if new_messages:
            # Load existing data
            existing_messages = await fetcher.data_manager.load_existing_data()
            
            # Deduplicate and combine
            all_messages = processor.deduplicate_messages(existing_messages, new_messages)
            
            # Save data
            await fetcher.data_manager.save_data(all_messages, len(new_messages))
            
            logger.info("✅ Successfully updated data.json")
        else:
            logger.warning("No new messages found")
            
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 