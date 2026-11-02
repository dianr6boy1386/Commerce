from decimal import Decimal

from django import forms

from .models import AuctionListing, Bid, Comment


class ListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ["title", "description", "starting_bid", "image_url", "category"]
        widgets = {
            "title": forms.TextInput(attrs={"autofocus": True}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "starting_bid": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://example.com/image.jpg"}),
        }

    def clean_starting_bid(self):
        starting_bid = self.cleaned_data["starting_bid"]
        if starting_bid < Decimal("0.01"):
            raise forms.ValidationError("Starting bid must be at least $0.01.")
        return starting_bid


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["amount"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})
        }

    def __init__(self, *args, min_amount=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_amount = min_amount
        if min_amount is not None:
            self.fields["amount"].widget.attrs["min"] = f"{min_amount:.2f}"

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if self.min_amount is not None and amount < self.min_amount:
            raise forms.ValidationError(f"Bid must be at least ${self.min_amount:.2f}.")
        return amount


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        labels = {"content": ""}
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add a comment"}
            )
        }

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Comment cannot be empty.")
        return content
