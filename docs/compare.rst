
.. _compare:

Comparing implementations
=========================
The following are simple, quite common views from a real world application.

.. |cbv| replace:: Django 1.3 Class-based generic views
.. |utkik| replace:: utkik.View

|cbv|::

    class ArtistDetail(DetailView):
        context_object_name = 'artist'
        queryset = Artist.publ.all()

|utkik|::

    class ArtistDetail(View):
        template = 'artists/artist_detail.html'

        def get(self, slug):
            self.c.artist = get_object_or_404(Artist.publ, slug=slug)

.. note:: The following two list views are written a little differently
          regarding the context collection to reflect more real world usage.

|cbv|::

    class ArtistList(TemplateView):
        template_name = 'artists/artist_list.html'

        def get_context_data(self, slug=None, tag=None):
            genre = get_object_or_404(Genre.objects, slug=slug)
            artists = Artist.publ.filter(genres=genre).order_by('?')
            tags = Tag.objects\
                .filter(artist__genres=genre, artist__active=True)\
                .annotate(num_tags=Count('artist'))\
                .filter(num_tags__gte=2)\
                .order_by('-num_tags')\
                .distinct()
            return {
                'artists': artists,
                'tags': tags,
                'selected_genre': genre,
            }

|utkik|::

    class ArtistList(View):
        template = 'artists/artist_list.html'

        def get(self, slug=None, tag=None):
            self.c.selected_genre = get_object_or_404(Genre.objects, slug=slug)
            self.c.artists = Artist.publ.filter(genres=self.c.selected_genre).order_by('?')
            self.c.tags = Tag.objects\
                .filter(artist__genres=self.c.selected_genre, artist__active=True)\
                .annotate(num_tags=Count('artist'))\
                .filter(num_tags__gte=2)\
                .order_by('-num_tags')\
                .distinct()

|cbv|::

    class MoreArtists(TemplateView):
        template_name = 'artists/inc/artists_in_focus.html'

        def dispatch(self, request, *args, **kwargs):
            if not request.is_ajax():
                return HttpResponseForbidden()
            return super(MoreArtists, self).dispatch(request, *args, **kwargs)

        def get_context_data(self):
            return { 'artists': Artist.publ.all().order_by('?')[:6] }

|utkik|::

    class MoreArtists(View):
        decorators = [ requires_ajax ]
        template = 'artists/inc/artists_in_focus.html'

        def get(self):
            self.c.artists = Artist.publ.all().order_by('?')[:6]

|cbv|::

    class ArtistLogin(FormView):
        form_class = ArtistLoginForm
        template_name = 'artists/login.html'

        def get(self, request, *args, **kwargs):
            request.session.set_test_cookie()
            return super(ArtistLogin, self).get(request, *args, **kwargs)

        def form_valid(self, form):
            login(self.request, form.artist)
            return HttpResponseRedirect(reverse('artist_mypage'))

        def get_form_kwargs(self):
            kwargs = super(ArtistLogin, self).get_form_kwargs()
            kwargs['request'] = self.request
            return kwargs

|utkik|::

    class ArtistLogin(View):
        template = 'artists/login.html'

        def get(self):
            self.request.session.set_test_cookie()
            self.c.form = ArtistLoginForm(request=self.request)

        def post(self):
            self.c.form = ArtistLoginForm(data=self.request.POST)
            if self.c.form.is_valid():
                login(self.request, self.c.form.artist)
                return HttpResponseRedirect(reverse('artist_mypage'))

|cbv|::

    from django.conf.urls.defaults import *
    from artists.views import ArtistDetail, ArtistList, ArtistTagList, MoreArtists, ArtistSearch, ArtistMyPage


    urlpatterns = patterns('',
        url(r'^min-sida/$', ArtistMyPage.as_view(), name='artist_mypage'),
        url(r'^artister/$', MoreArtists.as_view(), name='artist_more'),
        url(r'^artister/sok/$', ArtistSearch.as_view(), name='artist_search'),
        url(r'^artister/(?P<slug>[-\w]+)/$', ArtistList.as_view(), name='artist_genre_list'),
        url(r'^artister/(?P<slug>[-\w]+)/(?P<tag>.*)/$', ArtistTagList.as_view(), name='artist_genre_tag_list'),
        url(r'^(?P<slug>[-\w]+)/$', ArtistDetail.as_view(), name='artist_detail'),
    )

|utkik|::

    from utkik.dispatch import *


    urlpatterns = patterns('',
        url(r'^min-sida/$', 'artists.ArtistMyPage', name='artist_mypage'),
        url(r'^artister/$', 'artists.MoreArtists', name='artist_more'),
        url(r'^artister/sok/$', 'artists.ArtistSearch', name='artist_search'),
        url(r'^artister/(?P<slug>[-\w]+)/$', 'artists.ArtistList', name='artist_genre_list'),
        url(r'^artister/(?P<slug>[-\w]+)/(?P<tag>.*)/$', 'artists.ArtistTagList', name='artist_genre_tag_list'),
        url(r'^(?P<slug>[-\w]+)/$', 'artists.ArtistDetail', name='artist_detail'),
    )

.. note:: You can of course use the utkik dispatcher for |cbv| too.

