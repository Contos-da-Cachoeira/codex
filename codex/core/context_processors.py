from .models import SiteLayoutConfig


def layout_config(request):
    return {
        'layout_config': SiteLayoutConfig.load(),
    }
