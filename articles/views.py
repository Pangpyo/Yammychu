from django.shortcuts import render, redirect
from .models import Article, Comment, Team
from foods.models import Store, Review
from .forms import ArticleForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.core.paginator import Paginator  
from news import news
import json
from django.utils import timezone
from django.db.models import Count, Avg
from accounts.models import User
from django.views.decorators.http import require_http_methods, require_POST, require_safe

@require_safe
def index(request):
    teams = Team.objects.all()
    if request.user.is_authenticated and request.user.team :
        articles = Article.objects.filter(user__team=request.user.team).order_by('-pk')
    else :
        articles = Article.objects.order_by('-pk')
    ex_news = news().replace("<b>", "").replace("<\/b>", "").replace("&quot;", "'").replace("&apos;", "'")
    temp_news = json.loads(ex_news)
    store = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews'))
    store_review = store.order_by('-cnt_reviews')[:5]
    store_following = store.order_by('-cnt_followings')[:5]
    store_grade = store.order_by('-avg_grade')[:5]
    context = {
        "teams": teams,
        "articles":articles[:8],
        "temp_news": temp_news,
        "store_review": store_review,
        "store_grade": store_grade,
        "store_following": store_following,
    }
    return render(request, "articles/index.html", context)

@login_required
def create(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            article_form = ArticleForm(request.POST)
            if article_form.is_valid():
                article = article_form.save(commit=False)
                article.user = request.user
                article.save()
                return redirect('articles:community')
    else:
        article_form = ArticleForm()
    context = {
        "article_form": article_form,
    }
    return render(request, 'articles/create.html', context)

@login_required
def update(request, article_pk):
    article = Article.objects.get(pk=article_pk)
    if article.user == request.user:
        if request.method == "POST" and request.user.is_authenticated:
            article.updated_at = timezone.localtime()
            article.save()
            article_form = ArticleForm(request.POST, instance=article)
            if article_form.is_valid():
                article_form.save()
                return redirect("articles:detail", article_pk)
        else:
            article_form = ArticleForm(instance=article)
        context = {
            "article_form": article_form,
        }
        return render(request, 'articles/update.html', context)

@login_required
def delete(request, article_pk):
    article = Article.objects.get(pk=article_pk)
    if request.user == article.user:
        article.delete()
        return redirect('articles:community')

@login_required
def comments_create(request, article_pk):
    if request.user.is_authenticated:
        article = Article.objects.get(pk=article_pk)
        comment_form = CommentForm(request.POST)
        user = request.user.pk
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
        temp = Comment.objects.filter(article_id=article_pk).order_by('pk')
        comment_data = []
        for t in temp:
            comment_data.append({
                'userId': t.user_id, 
                'userName': t.user.username, 
                'nickname': t.user.nickname, 
                'logo': Team.objects.get(pk=t.user.team_id).logo.url,
                'content': t.content,
                'commentPk': t.pk,
            })
        context = {
            'comment_data': comment_data,
            'article_pk': article_pk,
            'user': user,
        }
    return JsonResponse(context)

@login_required
def comments_update(request, article_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    comment_username = comment.user.username
    user = request.user.pk
    jsonObject = json.loads(request.body)
    if request.method == 'POST':
        comment.content = jsonObject.get('content')
        comment.save()
    temp = Comment.objects.filter(article_id=article_pk).order_by('pk')
    comment_data = []
    for t in temp:
        comment_data.append({
            'userId':t.user_id, 
            'userName': t.user.username, 
            'nickname': t.user.nickname, 
            'logo': Team.objects.get(pk=t.user.team_id).logo.url,
            'content': t.content,
            'commentPk': t.pk,
        })
    context = {
        'comment_data': comment_data,
        'comment_pk': comment_pk,
        'comment_username': comment_username,
        'article_pk': article_pk,
        'user': user,
    }
    return JsonResponse(context)

@login_required
def comments_delete(request, article_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    article_pk = Article.objects.get(pk=article_pk).pk
    user = request.user.pk
    comment.delete()
    temp = Comment.objects.filter(article_id=article_pk).order_by('pk')
    comment_data = []
    for t in temp:
        comment_data.append({
            'userId':t.user_id, 
            'userName': t.user.username, 
            'nickname': t.user.nickname, 
            'logo': Team.objects.get(pk=t.user.team_id).logo.url,
            'content': t.content,
            'commentPk': t.pk,
        })
    context = {
        'comment_data': comment_data,
        'article_pk': article_pk,
        'user': user,
    }
    return JsonResponse(context)

@login_required
def like(request, article_pk):
    article = Article.objects.get(pk=article_pk)
    if article.user_article_like.filter(pk=request.user.pk).exists():
        article.user_article_like.remove(request.user)
        is_liked = False
    else:
        article.user_article_like.add(request.user)
        is_liked = True
    likeCount = article.user_article_like.count()
    article.like_count = likeCount
    context = {
        'isLiked' : is_liked,
        'likeCount' : article.user_article_like.count(),
    }
    return JsonResponse(context)


def community(request):
    articles = Article.objects.all().order_by('-pk')
    # ?????? ????????????
    page = request.GET.get("page", "1")
    # ?????????
    paginator_all = Paginator(articles, 10)
    page_obg_all = paginator_all.get_page(page)
    if request.user.is_authenticated:
        categorys = ['??????', '??????', '??????', '??????', '????????????', '??????', request.user.team.name ]
    else :
        categorys = ['??????', '??????', '??????', '??????', '????????????', '??????']
    context = {
        'articles' : articles,
        'articles_all' : page_obg_all,
        "categorys": categorys,
    }
    return render(request, 'articles/community.html', context)


def category(request, num):
    if request.user.is_authenticated:
        categorys = ['??????', '??????', '??????', '??????', '????????????', '??????', request.user.team.name ]
    else :
        categorys = ['??????', '??????', '??????', '??????', '????????????', '??????']
    category_name = categorys[num]
    if num <= 5 :
        articles_category = Article.objects.filter(category=category_name).order_by('-pk')
    else :
        team = Team.objects.get(name=category_name)
        articles_category = Article.objects.filter(user__team=team).order_by('-pk')

    page = request.GET.get("page", "1")
    paginator_category = Paginator(articles_category, 10)
    page_obg_category = paginator_category.get_page(page)
    context = {
        'articles_category' : page_obg_category,
        'categorys':categorys,
        "category_name":category_name,
    }
    return render(request, 'articles/category.html', context)



def detail(request, article_pk):
    article = Article.objects.get(pk=article_pk)
    comments = article.comment_set.all().order_by('pk')
    comment_form = CommentForm()
    context = {
        'article' : article,
        'comment_form' : comment_form,
        'comments' : comments,
    }
    return render(request, "articles/detail.html", context)