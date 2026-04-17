from datetime import datetime
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings


def _build_conf() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USER,
        MAIL_PASSWORD=settings.MAIL_PASS,
        MAIL_FROM=_extract_email(settings.MAIL_FROM),
        MAIL_FROM_NAME=_extract_name(settings.MAIL_FROM),
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


def _extract_email(addr: str) -> str:
    if "<" in addr and ">" in addr:
        return addr.split("<", 1)[1].split(">", 1)[0].strip()
    return addr.strip()


def _extract_name(addr: str) -> str:
    if "<" in addr:
        return addr.split("<", 1)[0].strip().strip('"')
    return ""


def generate_otp_html(full_name: str, otp_code: str) -> str:
    year = datetime.utcnow().year
    return f"""
  <body style="margin:0; padding:0; font-family:Arial, sans-serif; background-color:#f8f8f8;">
    <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background-color:#ffffff; margin:40px auto; border-radius:10px; overflow:hidden;">
      <tr style="background-color:#d32f2f;">
        <td style="padding:30px; text-align:center; color:#ffffff;">
          <h1 style="margin:0; font-size:24px;">Verify Your Email</h1>
        </td>
      </tr>
      <tr>
        <td style="padding:30px;">
          <p style="font-size:16px; color:#333;">Hi <strong>{full_name}</strong>,</p>
          <p style="font-size:16px; color:#333;">
            Use this One-Time Password (OTP) to verify your account:
          </p>
          <div style="background-color:#fce4ec; padding:15px; text-align:center; margin:20px 0; border:2px dashed #d32f2f; font-size:28px; letter-spacing:6px; color:#d32f2f; font-weight:bold;">
            {otp_code}
          </div>
          <p style="font-size:14px; color:#777;">This OTP will expire soon. Do not share it with anyone.</p>
          <hr style="border:none; border-top:1px solid #eee; margin:30px 0;">
          <p style="font-size:16px; color:#333;">
            Best regards,<br>
            <strong>The Fun Fin</strong>
          </p>
        </td>
      </tr>
      <tr style="background-color:#f5f5f5;">
        <td style="padding:20px; text-align:center; font-size:12px; color:#999;">
          &copy; {year} CLT Academy. All rights reserved.
        </td>
      </tr>
    </table>
  </body>
  """


async def send_email(to: str, subject: str, html: str) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=html,
        subtype=MessageType.html,
    )
    fm = FastMail(_build_conf())
    await fm.send_message(message)


async def send_otp_email(to: str, full_name: str, otp_code: str, subject: str = "Verify your email - OTP") -> None:
    html = generate_otp_html(full_name, otp_code)
    await send_email(to, subject, html)
