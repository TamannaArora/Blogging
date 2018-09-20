from __future__ import unicode_literals

import datetime
from datetime import date

from django import forms
from django.db import models

from django.utils.dateformat import DateFormat
from django.utils.formats import date_format
from django.shortcuts import redirect, render
from django.conf import settings

from wagtail.core import blocks
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel, StreamFieldPanel, FieldRowPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.tags import ClusterTaggableManager

from taggit.models import TaggedItemBase, Tag as TaggitTag

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.search import index

COMMENTS_APP = getattr(settings, 'COMMENTS_APP', None)

class BlogTagIndexPage(Page):

    def get_posts(self):
        posts = BlogPage.objects.live()
        return posts

    def get_context(self, request):
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)
        context = super().get_context(request)
        context['blogpages'] = blogpages
        context['top_stories'] = self.get_posts()[:5]
        return context


class BlogIndexPage(RoutablePageMixin, Page):
    intro = RichTextField(blank=True)
    poll = models.ForeignKey('blog.Poll', null=True, blank=True,
                on_delete=models.SET_NULL, related_name='+')

    # # Speficies that only BlogPage objects can live under this index page
    # subpage_types = ['BlogPage']

    @property
    def blogs(self):
        # Get list of blog pages that are descendants of this page
        blogs = BlogPage.objects.descendant_of(self).live()
        blogs = blogs.order_by(
            '-date'
        ).select_related('owner').prefetch_related(
            'tagged_items__tag',
            'categories',
            'categories__category',
        )
        return blogs
   
    def get_posts(self):
        posts = BlogPage.objects.live()
        return posts

    def get_context(self, request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        context = super(BlogIndexPage, self).get_context(request, *args, **kwargs)
        category = request.GET.get('key')
        # import pdb; pdb.set_trace()
        if not category:
            context['posts'] = self.get_posts()
        else:
            context['posts'] = self.get_posts().filter(categories__name__iexact=category)
        context['blog_page'] = self
        context['top_stories'] = self.get_posts().all().live()[5:]
        context['COMMENTS_APP'] = COMMENTS_APP
        return context

    @route(r'^tag/(?P<tag>[-\w]+)/$')
    def post_by_tag(self, request, tag, *args, **kwargs):
        self.search_type = 'tag'
        self.search_term = tag
        self.posts = self.get_posts().filter(tags__slug=tag)
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^$')
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return Page.serve(self, request, *args, **kwargs) 

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        SnippetChooserPanel('poll')
    ]



class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


@register_snippet
class Tag(TaggitTag):
    class Meta:
        proxy = True


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    slug = models.SlugField(max_length=80)
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name="children",
        help_text=(
            'Categories, unlike tags, can have a hierarchy. You might have a '
            'Jazz category, and under that have children categories for Bebop'
            ' and Big Band. Totally optional.'),
        on_delete=models.CASCADE,
)

    panels = [
        FieldPanel('name'),
        FieldPanel('parent'),
        FieldPanel('slug'),
        ImageChooserPanel('icon'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Blog Categories'

def get_blog_context(context):
    """ Get context data useful on all blog related pages """
    context['authors'] = get_user_model().objects.filter(
        owned_pages__live=True,
        owned_pages__content_type__model='blogpage'
    ).annotate(Count('owned_pages')).order_by('-owned_pages__count')
    context['all_categories'] = BlogCategory.objects.all()
    context['root_categories'] = BlogCategory.objects.filter(
        parent=None,
    ).prefetch_related(
        'children',
    ).annotate(
        blog_count=Count('blogpage'),
    )
    return context



class BlogPage(Page):
    date = models.DateTimeField("Post Date")
    intro = models.CharField(max_length=250)
    description = models.TextField()
    body =  models.TextField(blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)
    advert = models.ForeignKey('blog.Advert', null=True, blank=True,
                on_delete=models.SET_NULL, related_name='+')
    poll = models.ForeignKey('blog.Poll', null=True, blank=True,
                on_delete=models.SET_NULL, related_name='+')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='author_pages',
)

    @property
    def blog_page(self):
        return self.get_parent().specific

    # def get_absolute_url(self):
    #     # import pdb; pdb.set_trace()
    #     return self.url

    def get_posts(self):
        # import pdb; pdb.set_trace()
        posts = BlogPage.objects.live()[:5]
        return posts

    def get_context(self, request, *args, **kwargs):
        context = super(BlogPage, self).get_context(request, *args, **kwargs)
        # import pdb; pdb.set_trace()
        context['posts'] = self
        context['blog_page'] = self.get_parent().specific
        context['top_stories'] = self.get_posts()
        context['COMMENTS_APP'] = COMMENTS_APP
        context['menuitems'] = self.get_children().filter(
            live=True, show_in_menus=True)

        return context 

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
            FieldPanel('poll')
        ], heading="Blog Information"),
        FieldPanel('date'),
        FieldPanel('author'),
        FieldPanel('intro'),
        FieldPanel('description'),
        FieldPanel('body', classname="full"),
        InlinePanel('gallery_images', label="Gallery images"),
        SnippetChooserPanel('advert'),
    ]


    # Specifies parent to BlogPage as being BlogIndexPages
    # parent_page_types = ['BlogIndexPage']

    # Specifies what content types can exist as children of BlogPage.
    # Empty list means that no child content types are allowed.
    # subpage_types = []

class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE,
                       related_name="gallery_images")
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]

@register_snippet
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text

@register_snippet                                               
class Poll(models.Model):                                       
    intro = StreamField([                                       
        ('heading', blocks.CharBlock(classname='full title')),  
        ('html', blocks.RawHTMLBlock()),                        
        ('image', ImageChooserBlock()),                         
        ('paragraph', blocks.RichTextBlock()),                  
        ('video', EmbedBlock()),                                
    ])                                                          

    thank_you_text = StreamField([                              
        ('heading', blocks.CharBlock(classname='full title')),  
        ('html', blocks.RawHTMLBlock()),                        
        ('image', ImageChooserBlock()),                         
        ('paragraph', blocks.RichTextBlock()),                  
        ('video', EmbedBlock()),                                
    ])                                                          

    panels = [                                          
        # FieldPanel('title', classname='full title'),            
        StreamFieldPanel('intro'),                              
        # InlinePanel('form_fields', label='Questions'),          
        StreamFieldPanel('thank_you_text'),                     
    ]                                                           

class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='custom_form_fields')


class FormPage(AbstractEmailForm):
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        InlinePanel('custom_form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email Notification Config"),
    ]

    def get_form_fields(self):
        return self.custom_form_fields.all()