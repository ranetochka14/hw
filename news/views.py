from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page, cache_control
from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from .models import Article, NewsCategory, Product
from .serializers import ArticleSerializer, UserRegisterSerializer, UserSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Task
from .serializers import TaskSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

class LowLevelTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
        
            refresh['username'] = user.username
            refresh['is_staff_member'] = user.is_staff

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Неверные учетные данные'}, status=400)


def inspect_token_manually(raw_token):
    try:
        token = AccessToken(raw_token)
        
        user_id = token['user_id']
        username = token.get('username', 'Не указан')
        
        return {
            'status': 'valid',
            'user_id': user_id,
            'username': username,
            'expires_at': token['exp'] 
        }
    except Exception as e:
        return {
            'status': 'invalid',
            'error': str(e)
        }
class APIUserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, DjangoModelPermissions)

class APIArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


@cache_control(private=True, max_age=900)
def client_cached_page(request):
    return render(request, 'shop/client_cache_example.html', {
        'message': 'Эта страница кэшируется прямо в вашем браузере'
    })

def cached_products_view(request):
    cache_key = 'redis_product_list'
    products = cache.get(cache_key)

    if not products:
        products = list(Product.objects.all())
        cache.set(cache_key, products, timeout=300)

    return render(request, 'shop/product_list.html', {'products': products})

def home_view(request):
    latest_news = cache.get('latest_news_cache')
    if not latest_news:
        latest_news = list(Article.objects.order_by('-created_at')[:5])
        cache.set('latest_news_cache', latest_news, 300)

    popular_news = Article.objects.order_by('-views_count')[:5]

    return render(request, 'news/home.html', {
        'latest_news': latest_news,
        'popular_news': popular_news
    })

@cache_page(60)
def category_detail(request, slug):
    category = get_object_or_404(NewsCategory, slug=slug)
    articles = category.articles.all()
    return render(request, 'news/category_detail.html', {'category': category, 'articles': articles})

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.views_count += 1
    article.save(update_fields=['views_count'])
    return render(request, 'news/article_detail.html', {'article': article})

@api_view(['GET', 'POST'])
def task_list_create(request):
    """Получение списка всех задач или создание новой задачи."""
    if request.method == 'GET':
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def task_detail(request, pk):
    """Получение, обновление или удаление конкретной задачи по ID."""
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def user_list(request):
    """Выдача массива всех пользователей системы."""
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def user_create(request):
    """Создание нового пользователя."""
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def task_create(request):
    """Валидация полученных данных и сохранение задачи в базу данных."""
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)