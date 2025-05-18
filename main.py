import os
import asyncio
import email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import aiosmtplib
from aioimaplib import aioimaplib
from openai import AsyncOpenAI
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailGPTForwarder:
    def __init__(self):
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.imap_server = os.getenv('IMAP_SERVER')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def process_email_content(self, email_body: str, attachments: list) -> str:
        # Prepare the message for ChatGPT
        message = f"Email content:\n\n{email_body}\n\n"
        if attachments:
            message += "\nAttachments included:\n"
            for attachment in attachments:
                message += f"- {attachment['filename']}\n"
                if attachment['text_content']:
                    message += f"Content: {attachment['text_content'][:500]}...\n"

        # Get ChatGPT's response
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant processing email content. Provide a clear and concise response."},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting ChatGPT response: {e}")
            return f"Error processing with ChatGPT: {str(e)}"

    async def send_reply(self, to_address: str, subject: str, content: str):
        message = MIMEMultipart()
        message["From"] = self.email_username
        message["To"] = to_address
        message["Subject"] = f"Re: {subject}"
        
        message.attach(MIMEText(content, "plain"))

        try:
            async with aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port) as smtp:
                await smtp.starttls()
                await smtp.login(self.email_username, self.email_password)
                await smtp.send_message(message)
            logger.info(f"Reply sent to {to_address}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def extract_email_content(self, email_message):
        body = ""
        attachments = []

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'plain':
                    body += part.get_payload(decode=True).decode()
                elif part.get_content_maintype() != 'multipart':
                    filename = part.get_filename()
                    if filename:
                        content = part.get_payload(decode=True)
                        try:
                            text_content = content.decode('utf-8')
                        except:
                            text_content = None
                        attachments.append({
                            'filename': filename,
                            'content': content,
                            'text_content': text_content
                        })
        else:
            body = email_message.get_payload(decode=True).decode()

        return body, attachments

    async def check_emails(self):
        try:
            imap_client = aioimaplib.IMAP4_SSL(host=self.imap_server)
            await imap_client.wait_hello_from_server()
            await imap_client.login(self.email_username, self.email_password)
            await imap_client.select('INBOX')
            
            # Search for unread emails
            _, message_numbers = await imap_client.search('UNSEEN')
            message_numbers = message_numbers.decode().split()
            
            for num in message_numbers:
                _, msg_data = await imap_client.fetch(num, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_body = response_part[1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract sender and subject
                        from_address = email.utils.parseaddr(email_message['From'])[1]
                        subject = email_message['Subject']

                        # Process email content
                        body, attachments = self.extract_email_content(email_message)
                        
                        # Get ChatGPT response
                        gpt_response = await self.process_email_content(body, attachments)
                        
                        # Send reply
                        await self.send_reply(from_address, subject, gpt_response)
                        
                        # Mark email as read
                        await imap_client.store(num, '+FLAGS', '\\Seen')

            await imap_client.logout()
        except Exception as e:
            logger.error(f"Error checking emails: {e}")

    async def run(self):
        while True:
            await self.check_emails()
            await asyncio.sleep(self.check_interval)

async def main():
    forwarder = EmailGPTForwarder()
    await forwarder.run()

if __name__ == "__main__":
    asyncio.run(main())
