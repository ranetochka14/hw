from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import Article, NewsCategory
from django.shortcuts import render
from django.core.cache import cache
from .models import Product
from django.shortcuts import render
from django.views.decorators.cache import cache_control

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