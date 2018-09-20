from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from .blocks import BaseStreamBlock
from blog.models import BlogIndexPage, BlogPage

class StandardPage(Page):
    """
    A generic content page. On this demo site we use it for an about page but
    it could be used for any type of page content that only needs a title,
    image, introduction and body field
    """

    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Landscape mode only; horizontal width between 1000px and 3000px.'
    )
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )
    content_panels = Page.content_panels + [
        FieldPanel('introduction', classname="full"),
        StreamFieldPanel('body'),
        ImageChooserPanel('image'),
    ]

    # def get_context(self, request, *args, **kwargs):
    #     context = super().get_context(request)
    #     blogpages = self.get_children().live().order_by('-first_published_at')
    #     context['blogpages'] = blogpages
    #     return context


class HomePage(RoutablePageMixin, Page):
    #Hero section of Home Page
    banner_image = models.ForeignKey('wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    

    content_panels = [
        ImageChooserPanel('banner_image'),
        FieldPanel('title')
    ]
    def get_context(self, request):
        context = super().get_context(request)
        # blogpages = self.get_children().type(BlogPage).live().order_by('-first_published_at')
        blogpages = BlogPage.objects.all().order_by('-first_published_at')
        context['blogpages'] = blogpages
        context['top_stories'] = BlogPage.objects.all().live()
        return context

