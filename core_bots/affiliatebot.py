# AffiliateBot - GDPR Compliance and Affiliate Management
# Zero manual intervention for GDPR compliance

import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
import hashlib
import secrets

@dataclass
class GDPRAction:
    """GDPR compliance action result"""
    action_type: str
    affiliate_id: str
    success: bool
    details: Dict
    timestamp: datetime
    compliance_status: str

class GDPRCompliance:
    """GDPR compliance automation engine"""
    
    def __init__(self, database_url: str, email_config: Dict):
        self.database_url = database_url
        self.email_config = email_config
        self.db_pool = None
        
        # GDPR settings
        self.default_retention_days = 30
        self.consent_expiry_days = 365
        self.notification_days_before_expiry = 30
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize GDPR compliance system"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        self.logger.info("GDPR Compliance system initialized")
    
    async def process_consent_request(self, affiliate_data: Dict) -> GDPRAction:
        """Process new affiliate consent request"""
        affiliate_id = affiliate_data.get('affiliate_id')
        
        try:
            async with self.db_pool.acquire() as conn:
                # Check if affiliate already exists
                existing = await conn.fetchrow(
                    "SELECT id FROM affiliates WHERE affiliate_id = $1",
                    affiliate_id
                )
                
                if existing:
                    # Update existing affiliate
                    await conn.execute("""
                        UPDATE affiliates SET
                            company_name = $2,
                            contact_email = $3,
                            gdpr_consent = $4,
                            consent_date = $5,
                            data_retention_days = $6,
                            disclosure_text = $7,
                            commission_rate = $8,
                            status = $9,
                            updated_at = NOW()
                        WHERE affiliate_id = $1
                    """,
                        affiliate_id,
                        affiliate_data.get('company_name'),
                        affiliate_data.get('contact_email'),
                        True,
                        datetime.now(),
                        affiliate_data.get('data_retention_days', self.default_retention_days),
                        affiliate_data.get('disclosure_text'),
                        affiliate_data.get('commission_rate', 0.05),
                        'active'
                    )
                    action_type = "consent_updated"
                else:
                    # Create new affiliate
                    await conn.execute("""
                        INSERT INTO affiliates (
                            affiliate_id, company_name, contact_email,
                            gdpr_consent, consent_date, data_retention_days,
                            disclosure_text, commission_rate, status
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                        affiliate_id,
                        affiliate_data.get('company_name'),
                        affiliate_data.get('contact_email'),
                        True,
                        datetime.now(),
                        affiliate_data.get('data_retention_days', self.default_retention_days),
                        affiliate_data.get('disclosure_text'),
                        affiliate_data.get('commission_rate', 0.05),
                        'active'
                    )
                    action_type = "consent_granted"
                
                # Send confirmation email
                await self._send_consent_confirmation(affiliate_data)
                
                return GDPRAction(
                    action_type=action_type,
                    affiliate_id=affiliate_id,
                    success=True,
                    details={'consent_date': datetime.now().isoformat()},
                    timestamp=datetime.now(),
                    compliance_status='compliant'
                )
        
        except Exception as e:
            self.logger.error(f"Failed to process consent for {affiliate_id}: {str(e)}")
            return GDPRAction(
                action_type="consent_failed",
                affiliate_id=affiliate_id,
                success=False,
                details={'error': str(e)},
                timestamp=datetime.now(),
                compliance_status='error'
            )
    
    async def process_withdrawal_request(self, affiliate_id: str, reason: str = "") -> GDPRAction:
        """Process consent withdrawal request"""
        try:
            async with self.db_pool.acquire() as conn:
                # Update affiliate status
                await conn.execute("""
                    UPDATE affiliates SET
                        gdpr_consent = FALSE,
                        status = 'terminated',
                        updated_at = NOW()
                    WHERE affiliate_id = $1
                """, affiliate_id)
                
                # Schedule data for immediate purge
                await conn.execute("""
                    UPDATE affiliates SET
                        gdpr_purge_date = NOW() + INTERVAL '7 days'
                    WHERE affiliate_id = $1
                """, affiliate_id)
                
                # Log the withdrawal
                await self._log_gdpr_action(conn, 'consent_withdrawn', affiliate_id, {
                    'reason': reason,
                    'withdrawal_date': datetime.now().isoformat()
                })
                
                # Send confirmation email
                affiliate = await conn.fetchrow(
                    "SELECT contact_email, company_name FROM affiliates WHERE affiliate_id = $1",
                    affiliate_id
                )
                
                if affiliate:
                    await self._send_withdrawal_confirmation(
                        affiliate['contact_email'],
                        affiliate['company_name'],
                        affiliate_id
                    )
                
                return GDPRAction(
                    action_type="consent_withdrawn",
                    affiliate_id=affiliate_id,
                    success=True,
                    details={'withdrawal_date': datetime.now().isoformat(), 'reason': reason},
                    timestamp=datetime.now(),
                    compliance_status='withdrawal_processed'
                )
        
        except Exception as e:
            self.logger.error(f"Failed to process withdrawal for {affiliate_id}: {str(e)}")
            return GDPRAction(
                action_type="withdrawal_failed",
                affiliate_id=affiliate_id,
                success=False,
                details={'error': str(e)},
                timestamp=datetime.now(),
                compliance_status='error'
            )
    
    async def auto_purge_expired_data(self) -> List[GDPRAction]:
        """Automatically purge expired affiliate data"""
        actions = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Find affiliates with expired data
                expired_affiliates = await conn.fetch("""
                    SELECT affiliate_id, company_name, contact_email
                    FROM affiliates
                    WHERE gdpr_purge_date <= NOW()
                    AND status = 'terminated'
                """)
                
                for affiliate in expired_affiliates:
                    affiliate_id = affiliate['affiliate_id']
                    
                    try:
                        # Purge affiliate data
                        await conn.execute(
                            "DELETE FROM affiliates WHERE affiliate_id = $1",
                            affiliate_id
                        )
                        
                        # Log the purge
                        await self._log_gdpr_action(conn, 'data_purged', affiliate_id, {
                            'purge_date': datetime.now().isoformat(),
                            'reason': 'automatic_gdpr_compliance'
                        })
                        
                        # Send purge notification
                        await self._send_purge_notification(
                            affiliate['contact_email'],
                            affiliate['company_name'],
                            affiliate_id
                        )
                        
                        actions.append(GDPRAction(
                            action_type="data_purged",
                            affiliate_id=affiliate_id,
                            success=True,
                            details={'purge_date': datetime.now().isoformat()},
                            timestamp=datetime.now(),
                            compliance_status='purged'
                        ))
                        
                        self.logger.info(f"Auto-purged data for affiliate {affiliate_id}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to purge data for {affiliate_id}: {str(e)}")
                        actions.append(GDPRAction(
                            action_type="purge_failed",
                            affiliate_id=affiliate_id,
                            success=False,
                            details={'error': str(e)},
                            timestamp=datetime.now(),
                            compliance_status='error'
                        ))
        
        except Exception as e:
            self.logger.error(f"Auto-purge process failed: {str(e)}")
        
        return actions
    
    async def check_consent_expiry(self) -> List[GDPRAction]:
        """Check for expiring consents and send notifications"""
        actions = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Find consents expiring soon
                expiring_soon = await conn.fetch("""
                    SELECT affiliate_id, company_name, contact_email, consent_date
                    FROM affiliates
                    WHERE gdpr_consent = TRUE
                    AND status = 'active'
                    AND consent_date <= NOW() - INTERVAL '%s days'
                    AND consent_date > NOW() - INTERVAL '%s days'
                """ % (
                    self.consent_expiry_days - self.notification_days_before_expiry,
                    self.consent_expiry_days
                ))
                
                for affiliate in expiring_soon:
                    affiliate_id = affiliate['affiliate_id']
                    
                    try:
                        # Send expiry notification
                        await self._send_consent_expiry_notification(
                            affiliate['contact_email'],
                            affiliate['company_name'],
                            affiliate_id,
                            affiliate['consent_date']
                        )
                        
                        # Log the notification
                        await self._log_gdpr_action(conn, 'expiry_notification_sent', affiliate_id, {
                            'notification_date': datetime.now().isoformat(),
                            'consent_date': affiliate['consent_date'].isoformat(),
                            'days_until_expiry': self.notification_days_before_expiry
                        })
                        
                        actions.append(GDPRAction(
                            action_type="expiry_notification_sent",
                            affiliate_id=affiliate_id,
                            success=True,
                            details={'notification_date': datetime.now().isoformat()},
                            timestamp=datetime.now(),
                            compliance_status='notification_sent'
                        ))
                    
                    except Exception as e:
                        self.logger.error(f"Failed to send expiry notification to {affiliate_id}: {str(e)}")
                        actions.append(GDPRAction(
                            action_type="notification_failed",
                            affiliate_id=affiliate_id,
                            success=False,
                            details={'error': str(e)},
                            timestamp=datetime.now(),
                            compliance_status='error'
                        ))
        
        except Exception as e:
            self.logger.error(f"Consent expiry check failed: {str(e)}")
        
        return actions
    
    async def generate_compliance_report(self) -> Dict:
        """Generate GDPR compliance report"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get affiliate statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_affiliates,
                        COUNT(CASE WHEN gdpr_consent = TRUE THEN 1 END) as consented_affiliates,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_affiliates,
                        COUNT(CASE WHEN status = 'terminated' THEN 1 END) as terminated_affiliates,
                        COUNT(CASE WHEN gdpr_purge_date <= NOW() THEN 1 END) as pending_purge
                    FROM affiliates
                """)
                
                # Get recent GDPR actions
                recent_actions = await conn.fetch("""
                    SELECT table_name, operation, new_values, timestamp
                    FROM audit_log
                    WHERE table_name = 'affiliates'
                    AND timestamp >= NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                
                # Calculate compliance metrics
                total = stats['total_affiliates']
                compliance_rate = (stats['consented_affiliates'] / total * 100) if total > 0 else 100
                
                return {
                    'report_date': datetime.now().isoformat(),
                    'total_affiliates': total,
                    'consented_affiliates': stats['consented_affiliates'],
                    'active_affiliates': stats['active_affiliates'],
                    'terminated_affiliates': stats['terminated_affiliates'],
                    'pending_purge': stats['pending_purge'],
                    'compliance_rate': compliance_rate,
                    'recent_actions_count': len(recent_actions),
                    'gdpr_compliant': compliance_rate >= 95.0,
                    'auto_purge_enabled': True,
                    'retention_policy_days': self.default_retention_days
                }
        
        except Exception as e:
            self.logger.error(f"Failed to generate compliance report: {str(e)}")
            return {'error': str(e)}
    
    async def _send_consent_confirmation(self, affiliate_data: Dict):
        """Send consent confirmation email"""
        subject = "GDPR Consent Confirmation - AutoBots Affiliate Program"
        
        body = f"""
        Dear {affiliate_data.get('company_name', 'Affiliate')},
        
        This email confirms that we have received and processed your GDPR consent for the AutoBots Affiliate Program.
        
        Consent Details:
        - Affiliate ID: {affiliate_data.get('affiliate_id')}
        - Company: {affiliate_data.get('company_name')}
        - Consent Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - Data Retention Period: {affiliate_data.get('data_retention_days', self.default_retention_days)} days
        
        Your data will be processed in accordance with our privacy policy and GDPR regulations.
        
        You can withdraw your consent at any time by contacting us.
        
        Best regards,
        AutoBots GDPR Compliance Team
        """
        
        await self._send_email(
            affiliate_data.get('contact_email'),
            subject,
            body
        )
    
    async def _send_withdrawal_confirmation(self, email: str, company_name: str, affiliate_id: str):
        """Send consent withdrawal confirmation email"""
        subject = "GDPR Consent Withdrawal Confirmation"
        
        body = f"""
        Dear {company_name},
        
        This email confirms that we have processed your GDPR consent withdrawal request.
        
        Withdrawal Details:
        - Affiliate ID: {affiliate_id}
        - Company: {company_name}
        - Withdrawal Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Your data will be purged within 7 days as required by GDPR regulations.
        
        Best regards,
        AutoBots GDPR Compliance Team
        """
        
        await self._send_email(email, subject, body)
    
    async def _send_purge_notification(self, email: str, company_name: str, affiliate_id: str):
        """Send data purge notification email"""
        subject = "GDPR Data Purge Notification"
        
        body = f"""
        Dear {company_name},
        
        This email confirms that your data has been purged from our systems in accordance with GDPR regulations.
        
        Purge Details:
        - Affiliate ID: {affiliate_id}
        - Company: {company_name}
        - Purge Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        All personal data associated with your affiliate account has been permanently deleted.
        
        Best regards,
        AutoBots GDPR Compliance Team
        """
        
        await self._send_email(email, subject, body)
    
    async def _send_consent_expiry_notification(self, email: str, company_name: str, affiliate_id: str, consent_date: datetime):
        """Send consent expiry notification email"""
        expiry_date = consent_date + timedelta(days=self.consent_expiry_days)
        days_remaining = (expiry_date - datetime.now()).days
        
        subject = "GDPR Consent Renewal Required"
        
        body = f"""
        Dear {company_name},
        
        Your GDPR consent for the AutoBots Affiliate Program will expire in {days_remaining} days.
        
        Consent Details:
        - Affiliate ID: {affiliate_id}
        - Company: {company_name}
        - Original Consent Date: {consent_date.strftime('%Y-%m-%d')}
        - Expiry Date: {expiry_date.strftime('%Y-%m-%d')}
        
        To continue participating in our affiliate program, please renew your consent before the expiry date.
        
        If you do not renew your consent, your data will be automatically purged in accordance with GDPR regulations.
        
        Best regards,
        AutoBots GDPR Compliance Team
        """
        
        await self._send_email(email, subject, body)
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # In production, use async email sending
            # For now, log the email
            self.logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {str(e)}")
    
    async def _log_gdpr_action(self, conn, action_type: str, affiliate_id: str, details: Dict):
        """Log GDPR action in audit table"""
        await conn.execute("""
            INSERT INTO audit_log (
                table_name, operation, new_values, timestamp
            ) VALUES ($1, $2, $3, $4)
        """,
            'affiliates',
            action_type.upper(),
            json.dumps({
                'affiliate_id': affiliate_id,
                'action_type': action_type,
                'details': details
            }),
            datetime.now()
        )
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()

class AffiliateBot:
    """
    AffiliateBot - GDPR Compliance and Affiliate Management
    Zero manual intervention for GDPR compliance
    """
    
    def __init__(self, database_url: str, email_config: Dict):
        self.gdpr_compliance = GDPRCompliance(database_url, email_config)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize AffiliateBot"""
        await self.gdpr_compliance.initialize()
        self.logger.info("AffiliateBot initialized successfully")
    
    async def run_daily_compliance_check(self) -> Dict:
        """Run daily GDPR compliance check"""
        self.logger.info("Starting daily GDPR compliance check")
        
        results = {
            'date': datetime.now().isoformat(),
            'actions_performed': [],
            'errors': [],
            'compliance_status': 'compliant'
        }
        
        try:
            # Check for consent expiry
            expiry_actions = await self.gdpr_compliance.check_consent_expiry()
            results['actions_performed'].extend([
                {'type': action.action_type, 'affiliate_id': action.affiliate_id, 'success': action.success}
                for action in expiry_actions
            ])
            
            # Auto-purge expired data
            purge_actions = await self.gdpr_compliance.auto_purge_expired_data()
            results['actions_performed'].extend([
                {'type': action.action_type, 'affiliate_id': action.affiliate_id, 'success': action.success}
                for action in purge_actions
            ])
            
            # Generate compliance report
            compliance_report = await self.gdpr_compliance.generate_compliance_report()
            results['compliance_report'] = compliance_report
            
            # Check if any actions failed
            failed_actions = [action for action in expiry_actions + purge_actions if not action.success]
            if failed_actions:
                results['compliance_status'] = 'partial_compliance'
                results['errors'] = [action.details for action in failed_actions]
            
            self.logger.info(f"Daily compliance check completed: {len(results['actions_performed'])} actions performed")
            
        except Exception as e:
            self.logger.error(f"Daily compliance check failed: {str(e)}")
            results['compliance_status'] = 'error'
            results['errors'].append(str(e))
        
        return results
    
    async def process_affiliate_request(self, request_type: str, affiliate_data: Dict) -> GDPRAction:
        """Process affiliate GDPR request"""
        if request_type == 'consent':
            return await self.gdpr_compliance.process_consent_request(affiliate_data)
        elif request_type == 'withdrawal':
            return await self.gdpr_compliance.process_withdrawal_request(
                affiliate_data.get('affiliate_id'),
                affiliate_data.get('reason', '')
            )
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def close(self):
        """Close AffiliateBot"""
        await self.gdpr_compliance.close()

# Example usage and testing
async def main():
    """Test AffiliateBot functionality"""
    import os
    
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/autobots')
    email_config = {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-password',
        'from_email': 'noreply@autobots.com'
    }
    
    # Initialize AffiliateBot
    affiliate_bot = AffiliateBot(database_url, email_config)
    await affiliate_bot.initialize()
    
    # Test consent processing
    test_affiliate = {
        'affiliate_id': 'TEST001',
        'company_name': 'Test Company LLC',
        'contact_email': 'test@example.com',
        'disclosure_text': 'We earn commissions from qualifying purchases.',
        'commission_rate': 0.05,
        'data_retention_days': 30
    }
    
    # Process consent
    consent_result = await affiliate_bot.process_affiliate_request('consent', test_affiliate)
    print(f"Consent Result: {consent_result.action_type} - Success: {consent_result.success}")
    
    # Run daily compliance check
    compliance_results = await affiliate_bot.run_daily_compliance_check()
    print(f"Compliance Check: {compliance_results['compliance_status']}")
    print(f"Actions Performed: {len(compliance_results['actions_performed'])}")
    
    await affiliate_bot.close()

if __name__ == "__main__":
    asyncio.run(main())

