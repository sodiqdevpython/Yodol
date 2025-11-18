from django.db import models
from . import choices
import random
from .tasks import send_verify_email
from datetime import timedelta
from django.utils import timezone
from utils.models import BaseModel
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import FileExtensionValidator

nb = dict(null=True, blank=True)

class User(BaseModel, AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, **nb)
    first_name = models.CharField(max_length=30, **nb)
    last_name = models.CharField(max_length=30, **nb)
    birth_date = models.DateField(**nb)
    gender = models.CharField(max_length=6, choices=choices.GenderChoice.choices, **nb)
    profile_picture = models.ImageField(upload_to='profile_pictures/', **nb, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'], message="Faqat jpg, jpeg png rasm formatlari ruxsat etilgan.")
    ])
    
    auth_type = models.CharField(max_length=12, choices=choices.AuthTypeChoice.choices)
    auth_status = models.CharField(max_length=15, choices=choices.AuthStatusChoice.choices, default=choices.AuthStatusChoice.New)
    
    is_premium = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
    
    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def generate_username_and_password(self):
        self.username = self.id
        self.set_unusable_password()
    
    def create_confirm(self):
        if self.email:
            self.auth_type = choices.AuthTypeChoice.Email
        else:
            self.auth_type = choices.AuthTypeChoice.Phone
        
        UserConfirmation.objects.create(user=self, verify_type=self.auth_type)
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            if not self.is_superuser and not self.is_staff:
                self.generate_username_and_password()
                self.create_confirm()
        
                super().save(update_fields=['username', 'password', 'auth_type'])
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"


class UserConfirmation(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirmations')
    code = models.CharField(max_length=4, null=True, blank=True)
    verify_type = models.CharField(max_length=12, choices=choices.AuthTypeChoice.choices)
    expiration_time = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"
    
    def generate_code(self):
        self.code = random.randint(1000, 9999)
    
    def create_expiration(self):
        if self.verify_type == choices.AuthTypeChoice.Phone:
            self.expiration_time = timezone.now() + timedelta(minutes=2)
        else:
            self.expiration_time = timezone.now() + timedelta(minutes=5)
    
    def send_verify(self):
        print("Send verify ishlayabdi")
        if self.user.email:
            print("self.user.email bu to'g'ri ishladi")
            send_verify_email.delay(self.user.email, self.code, self.expiration_time)
            print("Bu ishladi send_verify_email.delay(self.user.email, self.code, self.expiration_time)")
        else:
            print(f"Hozircha telefonga yuborilmaydi faqat print qilaman: {self.user.email, self.code, self.expiration_time}")
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            self.generate_code()
            self.create_expiration()
            self.send_verify()
            print("send_verify chaqirildi")
        
        print(f"Natija: {self.user.email} / {self.user.phone_number} / code: {self.code} / {self.expiration_time}")
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"