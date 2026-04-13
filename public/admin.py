from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import Product, ProductVariant,ProductCategory,ProductMedia
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.utils.html import format_html


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category_image")
    list_display_links = ("name",)

    def category_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;" />',
                obj.image.url
            )
        return "—"

class ProductVariantInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        product = self.instance

        valid_variants = 0
        variants_missing_price = False

        for form in self.forms:
            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            valid_variants += 1

            # if ANY variant has no price → invalid
            if form.cleaned_data.get("price") is None:
                variants_missing_price = True

        # 🔴 must have at least one variant
        if valid_variants < 1:
            raise ValidationError(
                "At least one product variant is required."
            )

        # 🔴 price OR ALL variants must have price
        if product.price is None and variants_missing_price:
            raise ValidationError(
                "Set Product Price or provide a price for ALL variants."
            )
class ProductImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        valid_images = 0

        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE"):
                continue

            valid_images += 1

        if valid_images < 1:
            raise ValidationError("At least one product image is required.")

class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0
    formset = ProductImageInlineFormSet

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    formset = ProductVariantInlineFormSet


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline, ProductMediaInline]
    list_display = (
        "id",
        "title",
        "product_image", 
        "variant_sizes",
        "age_category",
        "product_category",
        "is_available",
        "created_at",
    )
    list_display_links = ("title",)

    list_filter = (
        "product_category",
        "age_category",
        "is_available",
        "created_at",
    )

    search_fields = ("title", "slug")

    def product_image(self, obj):
        main_media = obj.media.filter(is_main=True).first()

        if main_media and main_media.media:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit:cover;" />',
                main_media.media.url
            )
        return "—"

    def variant_sizes(self, obj):
        sizes = obj.variants.filter(is_available=True).values_list("size", flat=True)
        return ", ".join(sizes) if sizes else "—"

    variant_sizes.short_description = "Sizes"

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        product = form.instance

        # ✅ Apply common price
        if product.price is not None:
            product.variants.filter(price__isnull=True).update(
                price=product.price
            )

        # ✅ Apply common MRP (NEW 🔥)
        if product.mrp is not None:
            product.variants.filter(mrp__isnull=True).update(
                mrp=product.mrp
            )

        product.update_lowest_variant_prices()
