#!/usr/bin/env python3
"""
One-time script to fetch entire Telegram channel history
Filters for JSON messages and applies relevance filters
"""

import os
import json
import asyncio
import base64
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError, AuthKeyUnregisteredError
from telethon.tl.types import Message
import yaml

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_history_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security constants
SECURE_FILE_PERMISSIONS = 0o600
MAX_CONTENT_LENGTH = 2000
MAX_SOURCE_LENGTH = 500

# Allowed breach types
ALLOWED_BREACH_TYPES = [
    "Data leak", "Security breach", "Privacy violation", 
    "Ransomware", "Malware", "Phishing", "DDoS", "Other"
]

# Relevance filters
BREACH_INDICATORS = [
    'leak', 'breach', 'hack', 'compromise', 'exposed', 'stolen', 'database',
    'credentials', 'password', 'email', 'personal data', 'user data',
    'customer data', 'financial data', 'credit card', 'ssn', 'social security',
    'dump', 'database', 'records', 'accounts', 'users', 'customers',
    'financial', 'banking', 'payment', 'transaction', 'identity', 'personal',
    'address', 'phone', 'dob', 'date of birth', 'national id', 'passport'
]

SPAM_INDICATORS = [
    'buy', 'sell', 'offer', 'discount', 'promotion', 'service', 'tool',
    'software', 'review', 'rating', 'backlink', 'seo', 'marketing',
    'advertisement', 'sponsored', 'deal', 'sale', 'free trial', 'subscribe',
    'join', 'telegram.me', 't.me', 'channel', 'group', 'bot', 'premium'
]

class FullHistoryFetcher:
    """Fetch entire channel history with filtering"""
    
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.session_base64 = os.getenv('TELEGRAM_SESSION_BASE64')
        self.channel = os.getenv('CHANNEL', 'breachdetector')
        self.session_file = 'telegram_session.session'
        
    def create_session_file(self) -> bool:
        """Create session file from base64"""
        if not self.session_base64:
            logger.error("TELEGRAM_SESSION_BASE64 environment variable is required")
            return False
        
        try:
            # Validate base64 format
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', self.session_base64):
                logger.error("Invalid base64 format for session data")
                return False
            
            session_data = base64.b64decode(self.session_base64)
            
            with open(self.session_file, 'wb') as f:
                f.write(session_data)
            
            os.chmod(self.session_file, SECURE_FILE_PERMISSIONS)
            logger.info("✅ Session file created with secure permissions")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session file: {e}")
            return False
    
    def cleanup_session_file(self):
        """Securely cleanup session file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'wb') as f:
                    f.write(b'\x00' * os.path.getsize(self.session_file))
                os.remove(self.session_file)
                logger.info("✅ Session file securely cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up session file: {e}")
    
    def clean_text(self, text: str) -> str:
        """Clean message text"""
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
    
    def is_json_message(self, text: str) -> bool:
        """Check if message contains valid JSON"""
        try:
            clean_text = self.clean_text(text)
            
            # Try to parse as JSON
            for attempt in range(2):
                try:
                    parsed = json.loads(clean_text)
                    if isinstance(parsed, dict):
                        return True
                    elif isinstance(parsed, str):
                        clean_text = parsed
                        continue
                except json.JSONDecodeError:
                    break
            
            return False
        except Exception:
            return False
    
    def is_relevant_breach(self, content: str) -> bool:
        """Check if content is a relevant breach"""
        if not content:
            return False
            
        content_lower = content.lower()
        
        # Check for spam indicators
        spam_score = sum(1 for indicator in SPAM_INDICATORS 
                        if indicator in content_lower)
        
        # Check for breach indicators
        breach_score = sum(1 for indicator in BREACH_INDICATORS 
                          if indicator in content_lower)
        
        # Content is relevant if it has more breach indicators than spam
        return breach_score > spam_score and breach_score > 0
    
    def parse_json_message(self, message_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON message with validation"""
        try:
            if not isinstance(message_text, str):
                return None
                
            clean_text = self.clean_text(message_text)
            
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
                                elif key == 'Type':
                                    # Validate breach type
                                    if value not in ALLOWED_BREACH_TYPES:
                                        parsed[key] = "Other"
                        
                        # Check relevance
                        if self.is_relevant_breach(parsed.get('Content', '')):
                            return parsed
                        else:
                            logger.debug(f"Skipping non-relevant message: {parsed.get('Content', '')[:100]}...")
                            return None
                    
                    return None
                except json.JSONDecodeError:
                    break
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse message content: {e}")
            return None
    
    async def fetch_entire_history(self) -> List[Dict[str, Any]]:
        """Fetch entire channel history"""
        if not self.api_id or not self.api_hash:
            logger.error("API_ID and API_HASH environment variables are required")
            logger.error(f"API_ID: {'SET' if self.api_id else 'MISSING'}")
            logger.error(f"API_HASH: {'SET' if self.api_hash else 'MISSING'}")
            logger.error(f"SESSION_BASE64: {'SET' if self.session_base64 else 'MISSING'}")
            return []
        
        if not self.session_base64:
            logger.error("TELEGRAM_SESSION_BASE64 is required")
            return []
        
        try:
            # Create session file
            if not self.create_session_file():
                return []
            
            # Create client
            client = TelegramClient('telegram_session', self.api_id, self.api_hash)
            
            logger.info("Connecting to Telegram...")
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Session file is invalid or expired")
                return []
            
            logger.info(f"Fetching entire history from @{self.channel}...")
            
            # Get channel entity
            try:
                channel = await client.get_entity(f"@{self.channel}")
            except Exception as e:
                logger.error(f"Could not find channel @{self.channel}: {e}")
                return []
            
            # Fetch ALL messages (no limit)
            all_messages = []
            json_messages = 0
            relevant_messages = 0
            
            logger.info("Starting to fetch messages (this may take a while)...")
            
            async for message in client.iter_messages(channel, limit=None):  # No limit = all messages
                if message.text:
                    # Check if it's a JSON message
                    if self.is_json_message(message.text):
                        json_messages += 1
                        
                        # Parse and validate
                        parsed_content = self.parse_json_message(message.text)
                        if parsed_content:
                            # Add message metadata
                            parsed_content['message_id'] = message.id
                            parsed_content['timestamp'] = message.date.isoformat()
                            parsed_content['hash_id'] = hashlib.sha256(
                                parsed_content.get('Content', '').encode()
                            ).hexdigest()[:16]
                            
                            all_messages.append(parsed_content)
                            relevant_messages += 1
                            
                            # Log progress every 100 messages
                            if relevant_messages % 100 == 0:
                                logger.info(f"Processed {relevant_messages} relevant messages...")
            
            logger.info(f"✅ Fetch completed!")
            logger.info(f"   - Total messages processed: {len(list(client.iter_messages(channel, limit=None)))}")
            logger.info(f"   - JSON messages found: {json_messages}")
            logger.info(f"   - Relevant breach messages: {relevant_messages}")
            
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
            self.cleanup_session_file()
    
    def save_data(self, messages: List[Dict[str, Any]]):
        """Save filtered messages to data.json"""
        try:
            # Remove duplicates based on hash_id
            seen_hashes = set()
            unique_messages = []
            
            for msg in messages:
                hash_id = msg.get('hash_id')
                if hash_id and hash_id not in seen_hashes:
                    seen_hashes.add(hash_id)
                    unique_messages.append(msg)
            
            logger.info(f"Removed {len(messages) - len(unique_messages)} duplicates")
            
            # Sort by timestamp (newest first)
            unique_messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Save to file
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(unique_messages, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved {len(unique_messages)} unique relevant messages to data.json")
            
            # Create backup
            backup_file = f"data_backup_full_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(unique_messages, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Created backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")

async def main():
    """Main function"""
    logger.info("🚀 Starting full history fetch...")
    
    fetcher = FullHistoryFetcher()
    
    try:
        # Fetch entire history
        messages = await fetcher.fetch_entire_history()
        
        if messages:
            # Save filtered data
            fetcher.save_data(messages)
            logger.info("🎉 Full history fetch completed successfully!")
        else:
            logger.warning("No relevant messages found")
            
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 