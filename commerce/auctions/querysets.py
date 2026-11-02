from django.db.models import Count, QuerySet

from .models import AuctionListing


def with_bid_count(queryset: QuerySet[AuctionListing]) -> QuerySet[AuctionListing]:
    return queryset.annotate(bid_count=Count("bids", distinct=True))
