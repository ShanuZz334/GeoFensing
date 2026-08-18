import os
import resend
from flask import current_app

def send_credentials_email(teacher_email: str, teacher_name: str, reg_no: str, raw_password: str) -> bool:
    """
    Sends an email to the newly registered teacher with their login credentials
    using the Resend API.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    
    if not api_key:
        current_app.logger.error("RESEND_API_KEY is not set. Cannot send email.")
        return False
        
    resend.api_key = api_key
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; margin: 0; padding: 40px 20px;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            <tr>
                <td style="background-color: #7C3AED; padding: 32px 40px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">GeoFace</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 40px;">
                    <h2 style="margin-top: 0; color: #111827; font-size: 20px; font-weight: 600;">Welcome, {teacher_name}!</h2>
                    <p style="color: #4b5563; font-size: 16px; line-height: 24px; margin-bottom: 24px;">Your faculty account for the GeoFace Authentication System has been created successfully. Use the credentials below to access your account.</p>
                    
                    <div style="background-color: #f3f4f6; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 24px; margin-bottom: 32px;">
                        <p style="margin: 0 0 12px 0; font-size: 14px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Registration ID</p>
                        <p style="margin: 0 0 24px 0; font-size: 24px; color: #111827; font-weight: 700; letter-spacing: 1px; user-select: all;">{reg_no}</p>
                        
                        <p style="margin: 0 0 12px 0; font-size: 14px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Temporary Password</p>
                        <p style="margin: 0; font-size: 24px; color: #111827; font-weight: 700; letter-spacing: 2px; user-select: all;">{raw_password}</p>
                    </div>
                    
                    <p style="color: #4b5563; font-size: 16px; line-height: 24px; margin-bottom: 32px;">Please download the GeoFace app and log in using these credentials. You will be prompted to encode your face during your first login.</p>
                    
                    <div style="text-align: center;">
                        <a href="https://github.com/ShanuZz334/GeoFensing/releases/latest" style="display: inline-block; background-color: #7C3AED; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; padding: 14px 32px; border-radius: 8px; text-align: center;">Download GeoFace App</a>
                    </div>
                </td>
            </tr>
            <tr>
                <td style="background-color: #f9fafb; border-top: 1px solid #e5e7eb; padding: 24px 40px; text-align: center;">
                    <p style="margin: 0; color: #9ca3af; font-size: 14px;">If you did not request this account, please ignore this email or contact your administrator.</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    params = {
        "from": f"GeoFace Admin <{from_email}>",
        "to": [teacher_email],
        "subject": "Your GeoFace Faculty Credentials",
        "html": html_content,
    }
    
    try:
        response = resend.Emails.send(params)
        current_app.logger.info(f"Successfully sent credentials to {teacher_email}. Resend ID: {response.get('id')}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {teacher_email}: {str(e)}")
        return False
