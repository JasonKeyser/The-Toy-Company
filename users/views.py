from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from users.guest import is_guest_user
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required


def register(request):
    # where to send the player afterwards, e.g. ?next=/game/game_begin (only allow our own site)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        next_url = ''

    # a guest who signs up keeps the same User, so their games and stats carry over
    guest = request.user if is_guest_user(request.user) else None

    if request.method == 'POST':
        form = UserRegisterForm(request.POST, instance=guest)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            if guest:
                user.profile.is_guest = False
                user.profile.save()
                # the password just changed, so log in again to keep this browser signed in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Account created for {username}! Your guest games and stats were saved.')
                return redirect(next_url or 'game-history')
            messages.success(request, f'Account created for {username}! Log in to start playing.')
            login_url = reverse('login')
            return redirect(f'{login_url}?next={next_url}' if next_url else login_url)
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form, 'next': next_url, 'is_guest': bool(guest)})



@login_required
def profile(request):
    if is_guest_user(request.user):
        return redirect('register')

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/profile.html', context)




