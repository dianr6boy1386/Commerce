from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import AuctionListing, Bid, Category, Comment, User, Watchlist


class AuctionFlowTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", "seller@example.com", "pass12345")
        self.bidder = User.objects.create_user("bidder", "bidder@example.com", "pass12345")
        self.other = User.objects.create_user("other", "other@example.com", "pass12345")
        self.category, _ = Category.objects.get_or_create(name="Electronics")
        self.listing = AuctionListing.objects.create(
            title="Vintage Camera",
            description="A clean 35mm camera with lens.",
            starting_bid=Decimal("40.00"),
            current_price=Decimal("40.00"),
            image_url="",
            category=self.category,
            created_by=self.seller,
        )

    def test_index_shows_only_active_listings(self):
        AuctionListing.objects.create(
            title="Closed Item",
            description="Already sold.",
            starting_bid=Decimal("10.00"),
            current_price=Decimal("10.00"),
            created_by=self.seller,
            is_active=False,
        )

        response = self.client.get(reverse("index"))

        self.assertContains(response, "Vintage Camera")
        self.assertNotContains(response, "Closed Item")

    def test_create_listing_sets_creator_and_current_price(self):
        self.client.login(username="bidder", password="pass12345")

        response = self.client.post(
            reverse("create_listing"),
            {
                "title": "Desk Lamp",
                "description": "Brass lamp.",
                "starting_bid": "18.50",
                "image_url": "",
                "category": self.category.id,
            },
        )

        listing = AuctionListing.objects.get(title="Desk Lamp")
        self.assertRedirects(response, reverse("listing", args=[listing.id]))
        self.assertEqual(listing.created_by, self.bidder)
        self.assertEqual(listing.current_price, Decimal("18.50"))

    def test_first_bid_may_equal_starting_bid(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "40.00"})

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.current_price, Decimal("40.00"))
        self.assertEqual(Bid.objects.count(), 1)

    def test_bid_below_starting_bid_is_rejected(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "39.99"})

        self.assertEqual(Bid.objects.count(), 0)

    def test_later_bid_must_beat_current_price(self):
        Bid.objects.create(listing=self.listing, user=self.other, amount=Decimal("40.00"))
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "40.00"})

        self.listing.refresh_from_db()
        self.assertEqual(Bid.objects.count(), 1)

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "40.01"})

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.current_price, Decimal("40.01"))
        self.assertEqual(Bid.objects.count(), 2)

    def test_valid_bid_updates_listing(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "45.00"})

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.current_price, Decimal("45.00"))
        self.assertTrue(Bid.objects.filter(listing=self.listing, user=self.bidder).exists())

    def test_creator_cannot_bid_on_own_listing(self):
        self.client.login(username="seller", password="pass12345")

        self.client.post(reverse("place_bid", args=[self.listing.id]), {"amount": "45.00"})

        self.assertEqual(Bid.objects.count(), 0)

    def test_close_auction_sets_highest_bidder_as_winner(self):
        Bid.objects.create(listing=self.listing, user=self.bidder, amount=Decimal("55.00"))
        Bid.objects.create(listing=self.listing, user=self.other, amount=Decimal("60.00"))
        self.client.login(username="seller", password="pass12345")

        self.client.post(reverse("close_auction", args=[self.listing.id]))

        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)
        self.assertEqual(self.listing.winner, self.other)

    def test_non_owner_cannot_close_auction(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("close_auction", args=[self.listing.id]))

        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

    def test_watchlist_toggle_adds_and_removes_listing(self):
        self.client.login(username="bidder", password="pass12345")
        url = reverse("toggle_watchlist", args=[self.listing.id])

        self.client.post(url)
        self.assertTrue(Watchlist.objects.filter(user=self.bidder, listing=self.listing).exists())

        self.client.post(url)
        self.assertFalse(Watchlist.objects.filter(user=self.bidder, listing=self.listing).exists())

    def test_comment_requires_content(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("add_comment", args=[self.listing.id]), {"content": "   "})

        self.assertEqual(Comment.objects.count(), 0)

    def test_category_page_filters_active_listings(self):
        other_category, _ = Category.objects.get_or_create(name="Books")
        AuctionListing.objects.create(
            title="Novel",
            description="Hardcover.",
            starting_bid=Decimal("5.00"),
            current_price=Decimal("5.00"),
            category=other_category,
            created_by=self.seller,
        )

        response = self.client.get(reverse("category_listings", args=[self.category.id]))

        self.assertContains(response, "Vintage Camera")
        self.assertNotContains(response, "Novel")

    def test_index_shows_bid_count(self):
        Bid.objects.create(listing=self.listing, user=self.bidder, amount=Decimal("45.00"))

        response = self.client.get(reverse("index"))

        self.assertContains(response, "1 bid")

    def test_close_auction_with_no_bids_has_no_winner(self):
        self.client.login(username="seller", password="pass12345")

        self.client.post(reverse("close_auction", args=[self.listing.id]))

        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)
        self.assertIsNone(self.listing.winner)

        response = self.client.get(reverse("listing", args=[self.listing.id]))
        self.assertContains(response, "This auction closed with no winning bid.")
        self.assertContains(response, "No winning bid")

    def test_owner_can_delete_listing(self):
        self.client.login(username="seller", password="pass12345")

        response = self.client.post(reverse("delete_listing", args=[self.listing.id]))

        self.assertRedirects(response, reverse("index"))
        self.assertFalse(AuctionListing.objects.filter(pk=self.listing.id).exists())

    def test_non_owner_cannot_delete_listing(self):
        self.client.login(username="bidder", password="pass12345")

        self.client.post(reverse("delete_listing", args=[self.listing.id]))

        self.assertTrue(AuctionListing.objects.filter(pk=self.listing.id).exists())


class AuthTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass12345",
                "confirmation": "pass12345",
            },
        )

        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass12345",
                "confirmation": "different",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_login_with_valid_credentials(self):
        User.objects.create_user("alice", "alice@example.com", "pass12345")

        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "pass12345"},
        )

        self.assertRedirects(response, reverse("index"))

    def test_login_redirects_to_next(self):
        User.objects.create_user("alice", "alice@example.com", "pass12345")

        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "pass12345", "next": reverse("watchlist")},
        )

        self.assertRedirects(response, reverse("watchlist"))

    def test_login_ignores_external_next(self):
        User.objects.create_user("alice", "alice@example.com", "pass12345")

        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "pass12345", "next": "https://evil.example/"},
        )

        self.assertRedirects(response, reverse("index"))

    def test_login_with_invalid_credentials(self):
        User.objects.create_user("alice", "alice@example.com", "pass12345")

        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username and/or password.")


class WatchlistPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bidder", "bidder@example.com", "pass12345")
        self.seller = User.objects.create_user("seller", "seller@example.com", "pass12345")
        self.listing = AuctionListing.objects.create(
            title="Desk Chair",
            description="Ergonomic chair.",
            starting_bid=Decimal("25.00"),
            current_price=Decimal("25.00"),
            created_by=self.seller,
        )
        Watchlist.objects.create(user=self.user, listing=self.listing)

    def test_watchlist_page_requires_login(self):
        response = self.client.get(reverse("watchlist"))
        self.assertEqual(response.status_code, 302)

    def test_watchlist_page_lists_saved_items(self):
        self.client.login(username="bidder", password="pass12345")

        response = self.client.get(reverse("watchlist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desk Chair")


class MyAuctionsTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", "seller@example.com", "pass12345")
        self.bidder = User.objects.create_user("bidder", "bidder@example.com", "pass12345")
        self.listing = AuctionListing.objects.create(
            title="Closed Lamp",
            description="Sold lamp.",
            starting_bid=Decimal("10.00"),
            current_price=Decimal("15.00"),
            created_by=self.seller,
            is_active=False,
            winner=self.bidder,
        )

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("my_auctions")).status_code, 302)

    def test_winner_sees_won_auction_and_message(self):
        self.client.login(username="bidder", password="pass12345")

        page = self.client.get(reverse("my_auctions"))
        detail = self.client.get(reverse("listing", args=[self.listing.id]))

        self.assertContains(page, "Closed Lamp")
        self.assertContains(detail, "You won this auction.")

    def test_seller_sees_closed_listing_under_my_listings(self):
        self.client.login(username="seller", password="pass12345")

        page = self.client.get(reverse("my_auctions"))

        self.assertContains(page, "Closed Lamp")
