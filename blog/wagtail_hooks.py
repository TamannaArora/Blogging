
from wagtail.core import hooks

@hooks.register('construct_main_menu')
def hide_comments_menu_item_from_user(request, menu_items):
  if not request.user.is_superuser:
    menu_items[:] = [item for item in menu_items if item.name != 'comments']


@hooks.register('construct_explorer_page_queryset')
def show_my_profile_only(parent_page, pages, request):
    if request.user.is_authenticated():
        pages = pages.filter(owner=request.user)

    return pages



