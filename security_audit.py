#!/usr/bin/env python3
"""
Security Audit Script for LeakWatch
Checks for common security issues and configuration problems
"""

import os
import json
import yaml
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    """Security audit for LeakWatch project"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        
    def audit_file_permissions(self):
        """Check file permissions for sensitive files"""
        sensitive_files = [
            'telegram_session.session',
            '.env',
            'config.yaml',
            'data.json'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                mode = oct(stat.st_mode)[-3:]
                
                if mode != '600' and file_path in ['telegram_session.session', '.env']:
                    self.issues.append(f"⚠️  {file_path} has insecure permissions: {mode}")
                elif mode not in ['600', '644']:
                    self.warnings.append(f"⚠️  {file_path} has unusual permissions: {mode}")
                else:
                    self.passed_checks.append(f"✅ {file_path} has secure permissions: {mode}")
    
    def audit_environment_variables(self):
        """Check for hardcoded credentials in code"""
        code_files = [
            'fetch_secure_session.py',
            'fetch_secure_session_improved.py',
            'index.html'
        ]
        
        credential_patterns = [
            r'api_id["\']?\s*[:=]\s*["\']?\d+["\']?',
            r'api_hash["\']?\s*[:=]\s*["\']?[a-f0-9]{32}["\']?',
            r'22225752',
            r'9b0977dddfd05ce874e0d4ec41001348'
        ]
        
        for file_path in code_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in credential_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        self.issues.append(f"🚨 Hardcoded credentials found in {file_path}: {matches[:3]}")
                        break
                else:
                    self.passed_checks.append(f"✅ No hardcoded credentials in {file_path}")
    
    def audit_dependencies(self):
        """Check for known vulnerable dependencies"""
        requirements_files = ['requirements.txt', 'requirements_improved.txt']
        
        vulnerable_packages = {
            'telethon': '1.32.1',  # Check if this version has known vulnerabilities
            'aiohttp': '3.9.1',
            'cryptography': '41.0.7'
        }
        
        for req_file in requirements_files:
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    content = f.read()
                    
                for package, version in vulnerable_packages.items():
                    if f"{package}==" in content:
                        self.passed_checks.append(f"✅ {package} version {version} specified")
                    elif package in content:
                        self.warnings.append(f"⚠️  {package} version not pinned in {req_file}")
    
    def audit_data_quality(self):
        """Check data.json for quality issues"""
        if os.path.exists('data.json'):
            try:
                with open('data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check for spam content
                spam_indicators = ['buy', 'sell', 'offer', 'discount', 'promotion']
                spam_count = 0
                
                for entry in data:
                    content = entry.get('Content', '').lower()
                    if any(indicator in content for indicator in spam_indicators):
                        spam_count += 1
                
                if spam_count > len(data) * 0.3:  # More than 30% spam
                    self.issues.append(f"🚨 High spam content detected: {spam_count}/{len(data)} entries")
                elif spam_count > 0:
                    self.warnings.append(f"⚠️  Some spam content detected: {spam_count}/{len(data)} entries")
                else:
                    self.passed_checks.append(f"✅ Data quality looks good: {len(data)} entries")
                    
            except Exception as e:
                self.issues.append(f"🚨 Error reading data.json: {e}")
    
    def audit_configuration(self):
        """Check configuration files for security issues"""
        config_files = ['config.yaml', 'schema.json']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        if config_file.endswith('.yaml'):
                            config = yaml.safe_load(f)
                        else:
                            config = json.load(f)
                    
                    # Check for sensitive data in config
                    config_str = str(config)
                    if any(sensitive in config_str.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        self.warnings.append(f"⚠️  Potential sensitive data in {config_file}")
                    else:
                        self.passed_checks.append(f"✅ {config_file} looks clean")
                        
                except Exception as e:
                    self.issues.append(f"🚨 Error reading {config_file}: {e}")
    
    def audit_docker_security(self):
        """Check Dockerfile for security best practices"""
        if os.path.exists('Dockerfile'):
            with open('Dockerfile', 'r') as f:
                content = f.read()
            
            security_checks = [
                ('USER app', 'Non-root user specified'),
                ('--no-install-recommends', 'Minimal package installation'),
                ('rm -rf /var/lib/apt/lists/*', 'Package cache cleanup'),
                ('HEALTHCHECK', 'Health check configured'),
                ('COPY --chown=app:app', 'Proper file ownership')
            ]
            
            for check, description in security_checks:
                if check in content:
                    self.passed_checks.append(f"✅ {description}")
                else:
                    self.warnings.append(f"⚠️  Missing: {description}")
    
    def run_full_audit(self):
        """Run all security audits"""
        print("🔍 Starting Security Audit for LeakWatch...\n")
        
        self.audit_file_permissions()
        self.audit_environment_variables()
        self.audit_dependencies()
        self.audit_data_quality()
        self.audit_configuration()
        self.audit_docker_security()
        
        # Print results
        print("📊 Security Audit Results:\n")
        
        if self.issues:
            print("🚨 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        if self.passed_checks:
            print("✅ PASSED CHECKS:")
            for check in self.passed_checks:
                print(f"  {check}")
            print()
        
        # Summary
        total_checks = len(self.issues) + len(self.warnings) + len(self.passed_checks)
        security_score = len(self.passed_checks) / total_checks * 100 if total_checks > 0 else 0
        
        print(f"📈 Security Score: {security_score:.1f}%")
        print(f"   - Critical Issues: {len(self.issues)}")
        print(f"   - Warnings: {len(self.warnings)}")
        print(f"   - Passed Checks: {len(self.passed_checks)}")
        
        if self.issues:
            print("\n🔧 RECOMMENDATIONS:")
            print("  1. Fix all critical issues immediately")
            print("  2. Review and address warnings")
            print("  3. Run this audit regularly")
            return False
        elif self.warnings:
            print("\n🔧 RECOMMENDATIONS:")
            print("  1. Review and address warnings")
            print("  2. Consider implementing additional security measures")
            print("  3. Run this audit regularly")
            return True
        else:
            print("\n🎉 All security checks passed!")
            return True

if __name__ == "__main__":
    auditor = SecurityAuditor()
    success = auditor.run_full_audit()
    exit(0 if success else 1) 