from .models import Profile, SiteLayoutConfig


def _is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return getattr(getattr(user, 'profile', None), 'role', None) == Profile.UserRole.ADMIN


def layout_config(request):
    account_profile = None
    if request.user.is_authenticated:
        account_profile = Profile.objects.filter(user=request.user).first()

    return {
        'layout_config': SiteLayoutConfig.load(),
        'is_guildas': request.path.startswith('/guildas/'),
        'is_admin': _is_admin(request.user),
        'account_profile': account_profile,
    }
