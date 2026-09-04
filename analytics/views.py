from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

def increment_counter(key):
    if cache.get(key) is None:
        cache.set(key, 0)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1)
        return 1

def stats_view(request):
    page_visits = increment_counter('stats_page_visits')
    user_count = User.objects.count()
    product_views = cache.get('product_views_1', 0)

    context = {
        'page_visits': page_visits,
        'user_count': user_count,
        'product_views': product_views,
    }
    return render(request, 'analytics/stats.html', context)

def product_detail_stub_view(request, pk):
    increment_counter(f'product_views_{pk}')
    return redirect('stats')

def reset_stats_view(request):
    cache.delete_many(['stats_page_visits', 'product_views_1'])
    return redirect('stats')