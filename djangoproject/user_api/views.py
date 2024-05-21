from django.contrib.auth import get_user_model, login, logout
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Movie, AvailableSeat
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer, MovieSerializer, \
    AvailableSeatSerializer
from rest_framework import permissions, status, generics
from .validations import custom_validation, validate_email, validate_password
import json


@ensure_csrf_cookie
def set_csrf_token(request):
    return JsonResponse({'detail': 'CSRF cookie set'})


@csrf_exempt
def handle_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            if action == 'add_seat':
                return add_movie_screening_seat(data)
            elif action == 'reserve_seat':
                return reserve_movie_screening_seat(data)
            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


def add_movie_screening_seat(data):
    try:
        seat_number = data['seat_number']
        movie_screening_id = data['movie_screening_id']
        available = data['available']
        with connection.cursor() as cursor:
            cursor.execute("CALL AddMovieScreeningSeats(%s, %s, %s);", [seat_number, movie_screening_id, available])
        return JsonResponse({'message': 'Seat added successfully'}, status=201)
    except KeyError as e:
        return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def reserve_movie_screening_seat(data):
    try:
        seat_number = data['seat_number']
        movie_screening_id = data['movie_screening_id']
        available = data['available']
        with connection.cursor() as cursor:
            cursor.execute("CALL UpdateMovieScreeningSeat(%s, %s, %s);", [seat_number, movie_screening_id, available])
        return JsonResponse({'message': 'Seat reserved successfully'}, status=201)
    except KeyError as e:
        return JsonResponse({'error': f'Missing key: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class MovieList(generics.ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MovieDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class AvailableSeatsList(generics.ListAPIView):
    queryset = AvailableSeat.objects.all()
    serializer_class = AvailableSeatSerializer


class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        clean_data = custom_validation(request.data)
        serializer = UserRegisterSerializer(data=clean_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            login(request, user)
            return JsonResponse({'success': True, 'redirect_url': '/'}, status=status.HTTP_201_CREATED)
        return JsonResponse({'success': False, 'error': 'Failed to register'}, status=status.HTTP_400_BAD_REQUEST)


class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.data
        if not validate_email(data):
            return JsonResponse({'success': False, 'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)
        if not validate_password(data):
            return JsonResponse({'success': False, 'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.check_user(data)
            login(request, user)
            return JsonResponse({'success': True, 'redirect_url': '/'}, status=status.HTTP_200_OK)
        return JsonResponse({'success': False, 'error': 'Failed to log in'}, status=status.HTTP_400_BAD_REQUEST)


class UserLogout(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        logout(request)
        return JsonResponse({'success': True, 'redirect_url': '/login'}, status=status.HTTP_200_OK)


class UserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)
