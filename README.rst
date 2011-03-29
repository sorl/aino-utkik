
aino-utkik
==========

aino-utkik provides minimalistic class based views for Django focusing on
common usage, readability and convienience.

Example::

    # urls.py
    from utkik.dispatch import *

    urlpatterns = patterns('',
        (r'^(?<slug>[-\w]+)/$', 'news.NewsDetailView'),
        (r'^$', 'news.NewsListView'),
    )

    # news/views.py
    from django.shortcuts import get_object_or_404
    from news.models import News
    from utkik import BaseView

    class NewsDetailView(BaseView):
        template = 'news/news_detail.html'

        def get(self, slug):
            self.c.news = get_object_or_404(News.objects, slug=slug)


    class NewsDetailView(BaseView):
        template = 'news/news_list.html'

        def get(self, slug):
            self.c.news_list = News.objects.all()

