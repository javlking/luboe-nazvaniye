from django.shortcuts import render, redirect
from django.http import HttpResponse
from . import models
import telebot

# Create your views here.
def index(request):
    all_products = models.Product.objects.all()
    categories = models.Category.objects.all()
    return render(request, 'index.html', {'products': all_products, 'categories': categories})


def about(request):
    return HttpResponse('About us')


# GEt full info about product
def about_product(request, pk):
    product = models.Product.objects.get(product_name=pk)

    return render(request, 'about_product.html', {'product': product})


# Страница корзины
def user_cart(request):

    user_products = models.UserCart.objects.filter(user_id=request.user.id)

    total_amount = sum([total.quantity*total.product.product_price for total in user_products])

    return render(request, 'user_cart.html', {'products': user_products, 'total': total_amount})


# Добавление в корзину
def add_pr_to_cart(request, pk):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        user_id = request.user.id
        product_id = models.Product.objects.get(id=pk)

        if product_id.product_count > quantity:
            # Уменьшение количества на складе
            product_id.product_count -= quantity

            product_id.save()

            # Проверим есть ли вообще этот товар в корзине
            checker = models.UserCart.objects.filter(user_id=user_id, product=product_id)
            # Если нет такого товара то создаем
            if not checker:
                # Добавляем в корзину
                models.UserCart.objects.create(user_id=user_id, product=product_id, quantity=quantity)
            # Если есть то увеличим в количестве
            else:
                pr_to_add = models.UserCart.objects.get(user_id=user_id, product=product_id)
                pr_to_add.quantity += quantity
                pr_to_add.save()

            return redirect('/')

        else:
            return redirect(f'/product/{product_id.product_name}')


# Удаление из корзины
def delete_from_cart(request, pk):
    if request.method == 'POST':
        product_to_delete = models.Product.objects.get(id=pk)

        user_cart = models.UserCart.objects.get(product=product_to_delete, user_id=request.user.id)

        product_to_delete.product_count += user_cart.quantity

        user_cart.delete()

        product_to_delete.save()

        return redirect('/cart')

    return redirect('/')


# Отправить заказ в бот
def confirm_order(request, pk):
    if request.method == 'POST':
        user_cart = models.UserCart.objects.filter(user_id=request.user.id)

        full_message = 'Новый заказ:\n\n'

        for item in user_cart:
            full_message += f'Продукт: {item.product.product_name}: {item.quantity} шт\n'

        total = [i.product.product_price*i.quantity for i in user_cart]

        full_message += f'\n\nВсего за заказ: {sum(total)}'

        # Подключение к боту
        bot = telebot.TeleBot('BOT_TOKEN')

        bot.send_message(295612129, full_message)


        user_cart.delete()

        return redirect('/')