from flask_mail import Mail, Message
from flask import current_app
import random
import string

mail = Mail()


def generate_random_code():
    """GENERATE RANDOM CODE"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def send_verification_mail(email, code):
    """SEND VERIFICATION CODE"""
    try:
        msg = Message(
            "Email Verification",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=[email],
        )

        msg.body = f"your verivication code is: {code}"

        mail.send(msg)
        return True
    except Exception as ex:
        print(f"error sending verification code: {ex}")
        return False


def handle_email_verification(email):
    """CAN BE TRIGGERED DURING THE REGISTRATION PROCESS"""
    verification_code = generate_random_code()
    if send_verification_mail(email, verification_code):
        print("email sent successfully")
        return True
    else:
        print("failed sending email")
        return False
