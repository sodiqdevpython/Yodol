from rest_framework import serializers
from django.db.models import Q
from django.utils.timezone import now
from . import choices
from .models import User, UserConfirmation
import re
from django.contrib.auth.hashers import check_password


class SignUpSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.CharField(max_length=100, min_length=9, write_only=True)
    token = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['email_or_phone', 'token']
        extra_kwargs = {
            'token': {'read_only': True}
        }
    
    def get_token(self, obj):
        return obj.token()
    
    def validate_email_or_phone(self, data):
        if User.objects.filter(Q(email=data) | Q(phone_number=data)).exists():
            raise serializers.ValidationError("Bu akkaunt allaqachon mavjud")
        
        if data[1:len(data)].isdigit():
            if not bool(re.match("^\\+?[1-9][0-9]{7,14}$", data)):
                raise serializers.ValidationError("Telefon raqam validatsiyadan o'ta olmadi country code bilan bo'lsin masalan: +998990327898")
        elif "@" in data:
            if not bool(re.match(r"^\S+@\S+\.\S+$", data)):
                raise serializers.ValidationError("Email validatsiyadan o'tmadi")
        else:
            raise serializers.ValidationError("Kelgan qiymat email ham telefon raqam ham emas")
        
        return data
    
    def create(self, validated_data):
        email_or_phone = validated_data.pop('email_or_phone', None)
        
        if "@" in email_or_phone:
            user = User.objects.create(
                email=email_or_phone,
            )
        else:
            user = User.objects.create(
                phone_number=email_or_phone
            )
        
        return user
    
class VerifyUserSerializer(serializers.ModelSerializer):
    code = serializers.CharField(min_length=4, max_length=4, write_only=True)
    
    class Meta:
        model = UserConfirmation
        fields = ['code']
        
    def validate(self, data):
        user = self.context.get('user')
        code = data.pop('code', 0000)
        if user.auth_status != choices.AuthStatusChoice.New:
            raise serializers.ValidationError("Bu akkaunt allaqachon tasdiqlangan")
        
        user_confirm = UserConfirmation.objects.filter(
            user = user, code = code, is_used = False
        ).last()
        
        if not user_confirm:
            raise serializers.ValidationError("Tasdiqlash parolingiz xato ekan")
        
        if user_confirm and user_confirm.expiration_time < now():
            raise serializers.ValidationError("Kod to'g'ri lekin bu eskirgan yangi generate qiling")
        
        user_confirm.is_used = True
        user_confirm.save(update_fields=['is_used'])
        
        return data

class CreateUserMainInfoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'birth_date', 'gender', 'password', 'username']
        extra_kwargs = {
            'username': {'required': True},
            'password': {'required': True, 'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'birth_date': {'required': True},
            'gender': {'required': True},
        }
        
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        if password:
            instance.set_password(password)
        
        if instance.auth_status == choices.AuthStatusChoice.CodeVerified:
            instance.auth_status = choices.AuthStatusChoice.Done
        
        instance.save()
        
        return super().update(instance, validated_data)


class ChangeProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': False}
        }
    
    def validate(self, data):
        user = self.context.get('user', None)
        if user.auth_status not in [choices.AuthStatusChoice.Done, choices.AuthStatusChoice.Finished]:
            raise serializers.ValidationError("Akkauntingiz hali profile picture qo'yish darajasiga yetmagan sababi:\nAkkaunt yaratildi, CodeVerified qilingan lekin username, password qo'yilmagan undan keyin esa profile image ga o'ta olasiz")
        
        return data
    
    def update(self, instance, validated_data):
        if instance.auth_status == choices.AuthStatusChoice.Done:
            instance.auth_status = choices.AuthStatusChoice.Finished
            instance.save()
        
        return super().update(instance, validated_data)


class UserLoginSerializer(serializers.ModelSerializer):
    login_name = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)
    
    class Meta:
        model = User
        fields = ['login_name', 'password']
    
    def validate(self, attrs):
        login_name = attrs.get('login_name')
        user = User.objects.filter(Q(username=login_name) | Q(email=login_name) | Q(phone_number=login_name)).first()
        if not user or not check_password(attrs.get('password'), user.password):
            raise serializers.ValidationError("Invalid login credentials.")
        token = user.token()
        attrs['token'] = token
        return attrs