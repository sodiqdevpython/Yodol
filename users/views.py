from django.shortcuts import render
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from . import choices
from rest_framework.exceptions import ValidationError
from .models import UserConfirmation
from django.utils.timezone import now
from datetime import timedelta

class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(tags=["User authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email_or_phone': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={201: serializers.SignUpSerializer}
    )
    
    def post(self, request):
        get_data = request.data
        ser = serializers.SignUpSerializer(data=get_data)
        ser.is_valid(raise_exception=True)
        ser.save()
        
        return Response(
            {
                "message": "Yangi foydalanuvchi ayratildi",
                "data": ser.data
            }, status=status.HTTP_201_CREATED
        )

class UserVerifyView(APIView):
    @swagger_auto_schema(tags=["User authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={201: serializers.VerifyUserSerializer}
    )
    
    def post(self, request):
        user = request.user
        ser = serializers.VerifyUserSerializer(data = request.data, context = {'user': user})
        ser.is_valid(raise_exception=True)
        user.auth_status = choices.AuthStatusChoice.CodeVerified
        user.save(update_fields=['auth_status'])
        
        return Response(
            {
                "message": "Akkaunt tasdiqlandi !",
            }, status = status.HTTP_201_CREATED
        )

class GenerateNewVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=["User authentication"],
        operation_description="Yangi verify kod generatsiya qilish uchun endpoint.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="Kod yuborildi")
            }
        )}
    )

    
    def get(self, request):
        user = request.user
        if user.auth_status != choices.AuthStatusChoice.New:
            raise ValidationError("Akkaunt allaqachon tasdiqlangan")
        
        one_minute_ago = now() - timedelta(minutes=1)
        count_last_hour = UserConfirmation.objects.filter(
            user=user,
            created_at__gte=one_minute_ago
        ).count()
        
        if count_last_hour > 1:
            raise ValidationError("Ko'p yuborayabsiz 1 minutda faqat bitta verification code yuboraman 1 minut kuting")
        
        UserConfirmation.objects.create(
            user = user, verify_type = user.auth_type
        )
        
        return Response(
            {
                "message": "Emailga qarang kod yuborildi",
                "token": user.token()
            }
        )
        
class ChangeUserMainInfoView(APIView):
    @swagger_auto_schema(tags=["User authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name' : openapi.Schema(type=openapi.TYPE_STRING),
                'last_name' : openapi.Schema(type=openapi.TYPE_STRING),
                'birth_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date',
                    example="2005-08-13"
                ),
                'gender': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=[choice[0] for choice in choices.GenderChoice.choices]
                )
            }
        ),
        responses={201: serializers.CreateUserMainInfoSerializer}
    )
    
    def patch(self, request):
        user = request.user
        if user.auth_status != choices.AuthStatusChoice.CodeVerified:
            raise ValidationError("Bu akkaunt ma'lumotlari allaqachon kiritilgan")
        
        ser = serializers.CreateUserMainInfoSerializer(instance=request.user, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        
        return Response(
            {
                "message": "Akkaunt yangilandi",
                "data": ser.data
            }
        )

class ChangeProfilePicture(APIView):
    @swagger_auto_schema(
        tags=["User authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'profile_picture': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        }
    )
    
    def put(self, request):
        ser = serializers.ChangeProfilePictureSerializer(instance=request.user, data=request.data, context = {'user': request.user})
        ser.is_valid(raise_exception=True)
        ser.save()
        
        return Response(
            {
                "message": "Account finished",
                "data": ser.data
            }, status=status.HTTP_200_OK
        )
        
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(tags=["User authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'login_name': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: serializers.UserLoginSerializer}
    )
    
    def post(self, request):
        if request.user.is_authenticated:
            token = request.user.token()
            return Response(
                {
                    "status": False,
                    "message": "User is already logged in.",
                    "data": {
                        "token": token
                    }
                }, status=400
            )
        ser = serializers.UserLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        get_token = ser.validated_data['token']
        return Response(
            {
                "status": True,
                "message": "User logged in successfully",
                "data": {
                    "token": get_token
                }
            }, status=200
        )

class ProfileInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    
    @swagger_auto_schema(
        operation_summary="Foydalanuvchi profili",
        operation_description=(
            "Autentifikatsiyadan o‘tgan foydalanuvchining "
            "profil ma'lumotlarini qaytaradi."
        ),
        tags=["User authentication"],
        responses={
            200: openapi.Response(
                description="Foydalanuvchi ma'lumotlari muvaffaqiyatli olindi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Foydalanuvchi ma'lumotlari"
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "username": openapi.Schema(type=openapi.TYPE_STRING, example="sodiq"),
                                "email": openapi.Schema(type=openapi.TYPE_STRING, example="sodiq@gmail.com"),
                            }
                        ),
                    }
                )
            ),
            401: openapi.Response(
                description="Autentifikatsiya qilinmagan"
            )
        }
    )
    def get(self, request):
        ser = serializers.UserProfileSerializer(instance=request.user)
        return Response(
            {
                "message": "Foydalanuvchi ma'lumotlari",
                "data": ser.data
            }
        )