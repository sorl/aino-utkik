
aino-utkik
==========

aino-utkik provides minimalistic class based views for Django focusing on
common usage, readability and convienience.

Example::

    # urls.py
    from utkik.dispatch import *

    urlpatterns = patterns('',
        (r'^(?P<slug>[-\w]+)/$', 'news.NewsDetailView'),
        (r'^$', 'news.NewsListView'),
    )

    # news/views.py
    from django.shortcuts import get_object_or_404
    from news.models import News
    from utkik import View

    class NewsDetailView(View):
        template_name = 'news/news_detail.html'

        def get(self, slug):
            self.c.news = get_object_or_404(News.objects, slug=slug)


    class NewsListView(View):
        template_name = 'news/news_list.html'

        def get(self):
            self.c.news_list = News.objects.all()

