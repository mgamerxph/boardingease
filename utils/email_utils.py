from django.core.mail import send_mail

def send_approval_email(to_email, owner_name):
    subject = "Your BoardingEase Account Has Been Approved"
    message = f"""
Hi {owner_name},

Your account on BoardingEase has been approved by the administrator. 
You can now log in and start managing your boarding house.

Login here: https://https://mgamerxph.pythonanywhere.com/login

Thank you,
BoardingEase Team
"""
    send_mail(subject, message, None, [to_email])
