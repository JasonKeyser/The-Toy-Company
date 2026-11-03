"""Guest accounts: let people play Freeplay without signing up.

A guest is a normal Django User with an unusable password and profile.is_guest = True.
Every game view keeps working because the guest is logged in like anyone else.
If the guest registers later, register() upgrades this same User, so their games are kept.
"""
import secrets

from django.contrib.auth import login
from django.contrib.auth.models import User


def is_guest_user(user):
    if not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)
    return bool(profile and profile.is_guest)


def create_guest_user(request):
    """Create a throwaway account, log it in for this browser, and return it."""
    username = f"guest-{secrets.token_hex(4)}"
    while User.objects.filter(username=username).exists():
        username = f"guest-{secrets.token_hex(4)}"

    user = User(username=username)
    user.set_unusable_password()
    user.save()                    # users/signals.py creates the Profile here
    user.profile.is_guest = True
    user.profile.save()

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return user