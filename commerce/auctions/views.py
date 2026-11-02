from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import BidForm, CommentForm, ListingForm
from .models import AuctionListing, Bid, Category, Comment, User, Watchlist
from .querysets import with_bid_count


def index(request):
    listings = with_bid_count(
        AuctionListing.objects.filter(is_active=True).select_related("category", "created_by")
    )
    return render(request, "auctions/index.html", {"listings": listings})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        next_url = request.POST.get("next", "")
        if user is not None:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return HttpResponseRedirect(next_url)
            return HttpResponseRedirect(reverse("index"))

        return render(
            request,
            "auctions/login.html",
            {"message": "Invalid username and/or password.", "next": next_url},
        )

    return render(request, "auctions/login.html", {"next": request.GET.get("next", "")})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(
                request,
                "auctions/register.html",
                {"message": "Passwords must match."},
            )

        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )

        login(request, user)
        return HttpResponseRedirect(reverse("index"))

    return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.created_by = request.user
            listing.current_price = listing.starting_bid
            listing.save()
            messages.success(request, "Listing created.")
            return redirect("listing", listing_id=listing.id)
    else:
        form = ListingForm()

    return render(request, "auctions/create_listing.html", {"form": form})


def listing_detail(request, listing_id):
    listing = get_object_or_404(
        with_bid_count(
            AuctionListing.objects.select_related("category", "created_by", "winner")
        ),
        pk=listing_id,
    )
    bids = listing.bids.select_related("user")
    comments = listing.comments.select_related("user")
    is_watched = False

    if request.user.is_authenticated:
        is_watched = Watchlist.objects.filter(user=request.user, listing=listing).exists()

    return render(
        request,
        "auctions/listing.html",
        {
            "listing": listing,
            "bids": bids,
            "comments": comments,
            "is_watched": is_watched,
            "is_winner": listing.winner_id == getattr(request.user, "id", None),
            "bid_form": BidForm(min_amount=listing.next_bid),
            "comment_form": CommentForm(),
            "min_bid": listing.next_bid,
        },
    )


@login_required
@require_POST
def place_bid(request, listing_id):
    with transaction.atomic():
        listing = get_object_or_404(
            AuctionListing.objects.select_for_update(), pk=listing_id
        )

        form = BidForm(request.POST, min_amount=listing.next_bid)
        if not listing.is_active:
            messages.error(request, "This auction is closed.")
        elif request.user == listing.created_by:
            messages.error(request, "You cannot bid on your own listing.")
        elif form.is_valid():
            amount = form.cleaned_data["amount"].quantize(Decimal("0.01"))
            Bid.objects.create(listing=listing, user=request.user, amount=amount)
            listing.current_price = amount
            listing.save(update_fields=["current_price"])
            messages.success(request, "Bid placed.")
        else:
            messages.error(request, form.errors.get("amount", ["Invalid bid."])[0])

    return redirect("listing", listing_id=listing_id)


@login_required
@require_POST
def close_auction(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)

    if request.user != listing.created_by:
        messages.error(request, "Only the creator can close this auction.")
    elif not listing.is_active:
        messages.error(request, "This auction is already closed.")
    else:
        highest_bid = listing.bids.order_by("-amount", "-created_at").first()
        listing.winner = highest_bid.user if highest_bid else None
        listing.is_active = False
        listing.save(update_fields=["winner", "is_active"])
        messages.success(request, "Auction closed.")

    return redirect("listing", listing_id=listing.id)


@login_required
@require_POST
def delete_listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)

    if request.user != listing.created_by:
        messages.error(request, "Only the creator can delete this listing.")
        return redirect("listing", listing_id=listing.id)

    listing.delete()
    messages.success(request, "Listing deleted.")
    return redirect("index")


@login_required
@require_POST
def add_comment(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        Comment.objects.create(
            listing=listing,
            user=request.user,
            content=form.cleaned_data["content"],
        )
        messages.success(request, "Comment added.")
    else:
        messages.error(request, form.errors.get("content", ["Invalid comment."])[0])

    return redirect("listing", listing_id=listing.id)


@login_required
def watchlist(request):
    listings = with_bid_count(
        AuctionListing.objects.filter(watchers__user=request.user)
        .select_related("category", "created_by")
        .order_by("-created_at")
    )
    return render(request, "auctions/watchlist.html", {"listings": listings})


@login_required
def my_auctions(request):
    base = AuctionListing.objects.select_related("category", "created_by", "winner").order_by("-created_at")
    won = with_bid_count(base.filter(winner=request.user))
    selling = with_bid_count(base.filter(created_by=request.user))
    return render(request, "auctions/my_auctions.html", {"won": won, "selling": selling})


@login_required
@require_POST
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    entry, created = Watchlist.objects.get_or_create(user=request.user, listing=listing)

    if created:
        messages.success(request, "Added to watchlist.")
    else:
        entry.delete()
        messages.success(request, "Removed from watchlist.")

    return redirect("listing", listing_id=listing.id)


def categories(request):
    all_categories = Category.objects.all()
    return render(request, "auctions/categories.html", {"categories": all_categories})


def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = with_bid_count(
        AuctionListing.objects.filter(category=category, is_active=True)
        .select_related("category", "created_by")
        .order_by("-created_at")
    )
    return render(
        request,
        "auctions/category_listings.html",
        {"category": category, "listings": listings},
    )
