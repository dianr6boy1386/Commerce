from django.contrib import admin

from .models import AuctionListing, Bid, Category, Comment, User, Watchlist


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "category", "current_price", "is_active", "winner")
    list_filter = ("is_active", "category")
    search_fields = ("title", "description", "created_by__username")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("listing__title", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "created_at")
    search_fields = ("listing__title", "user__username", "content")


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "listing")
    search_fields = ("user__username", "listing__title")
