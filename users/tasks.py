from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verify_email(email, code, expiration_time):
    print("Task boshlandi ------")
    print(f"Mana: {email} {code} {expiration_time}")
    subject = "Xush kelibsiz !"
    message = f"Akkauntingizni aktivlashtirish uchun parol: {code}\nparol amal qilish muddati: {expiration_time} gacha"
    send_mail(subject, message, None, [email])
    print("Task tugadi -----")