from django.shortcuts import render, get_object_or_404, redirect
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, Category

def product_list(request):
    products = cache.get('all_products_list')
    if not products:
        products = list(Product.objects.select_related('category').all())
        cache.set('all_products_list', products, 60) 
    return render(request, 'shop/product_list.html', {'products': products})

def product_detail(request, pk):
    cache_key = f'product_detail_{pk}'
    product = cache.get(cache_key)
    if not product:
        product = get_object_or_404(Product, pk=pk)
        cache.set(cache_key, product, 120) 
    return render(request, 'shop/product_detail.html', {'product': product})

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    return render(request, 'shop/category_products.html', {'category': category, 'products': products})

@staff_member_required
def clear_cache_view(request):
    cache.clear()
    return redirect('product_list')