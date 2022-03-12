from django.contrib.auth.models import User
from django.db.models import Prefetch

from django.db import models
from django.db.models import Count
from django.urls import reverse

# Колдуй тут↓↓


class TagQuerySet(models.QuerySet):
    def fetch_with_posts(self):
        tag_ids = [tag.id for tag in self]
        tags_with_posts = Tag.objects\
            .filter(id__in=tag_ids)\
            .annotate(posts_amount=Count('posts'))

        ids_and_posts = tags_with_posts.values_list(
            'id', 'posts_amount')
        count_for_id = dict(ids_and_posts)
        for tag in self:
            tag.posts_amount = count_for_id[tag.id]
        return self

    def popular(self):
        tags = self\
            .annotate(posts_amount=Count('posts'))\
            .order_by('-posts_amount')
        return tags


class PostQuerySet(models.QuerySet):
    def popular(self):
        popular_posts = self\
            .annotate(likes_amount=Count('likes', distinct=True))\
            .order_by('-likes_amount')
        return popular_posts

    def fetch_with_comments(self):
        posts_ids = [post.id for post in self]
        posts_with_comments = Post.objects\
            .filter(id__in=posts_ids)\
            .annotate(comments_amount=Count('comments'))

        ids_and_comments = posts_with_comments.values_list(
            'id', 'comments_amount')
        count_for_id = dict(ids_and_comments)
        for post in self:
            post.comments_amount = count_for_id[post.id]
        return self


class Post(models.Model):
    objects = PostQuerySet.as_manager()

    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    objects = TagQuerySet.as_manager()

    title = models.CharField('Тег', max_length=20, unique=True)

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
