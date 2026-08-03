"""
Public legal pages required by the Google Play / App Store listings.

Both must be reachable WITHOUT authentication and without installing the
app -- that is the whole point of them as far as the stores are concerned:

  * Privacy policy      -> required for every Play listing.
  * Account deletion    -> required because the app lets users create an
                           account (see the mobile signup screen). Google
                           requires a web route where deletion can be
                           requested by someone who cannot, or will not,
                           install the app. The in-app
                           "Supprimer mon compte" button does not satisfy
                           this on its own.

Content is kept in sync with the mobile app's own screens
(lib/presentation/screens/shared/settings/privacy_policy_screen.dart) --
Play compares the two, and a contradiction between them is a rejection
cause. Update both together.
"""
from django.views.decorators.cache import never_cache
from django.shortcuts import render


@never_cache
def privacy_policy(request):
    return render(request, 'legal/privacy_policy.html')


@never_cache
def account_deletion(request):
    return render(request, 'legal/account_deletion.html')
