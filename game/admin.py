from django.contrib import admin
from .models import Post, Toy, Player, Difficulty, AdvertisingProfile, InsuranceEvent, Equipment, InterestRateProfile

admin.site.register(Post)
admin.site.register(Toy)
admin.site.register(Player)
admin.site.register(Difficulty)
admin.site.register(AdvertisingProfile)
admin.site.register(InsuranceEvent)
admin.site.register(Equipment)
admin.site.register(InterestRateProfile)