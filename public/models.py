from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True,editable=False) 

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # ✅ ensure unique slug
            while ProductCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

class Product(models.Model):

    AGE_CATEGORY_CHOICES = [
        ('baby_boy', 'Baby - Boy'),
        ('baby_girl', 'Baby - Girl'),
        ('baby_unisex', 'Baby - Unisex'),
        ('kids_boy', 'Kids - Boy'),
        ('kids_girl', 'Kids - Girl'),
        ('kids_unisex', 'Kids - Unisex'),
        ('adults_men', 'Adults - Men'),
        ('adults_women', 'Adults - Women'),
        ('adults_unisex', 'Adults - Unisex'),
        ('all_age_men', 'All Age - Men'),
        ('all_age_women', 'All Age - Women'),
        ('all_age_unisex', 'All Age - Unisex'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True,editable=False)
    age_category = models.CharField(
        max_length=20,
        choices=AGE_CATEGORY_CHOICES,
        default='baby_unisex'
    )
    product_category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products'
    )
    material_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True,null=True)
    features = models.TextField(blank=True,null=True,help_text="◉ Separate features with new lines for better display on frontend.")


    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Use it only when all variants have the same mrp"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Use it only when all variants have the same price"
    )

    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0
    )

    size_guide = models.FileField(upload_to="products/",blank=True, null=True)
    lowest_variant_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        editable=False
    )

    lowest_variant_mrp = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        editable=False
    )

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def update_lowest_variant_prices(self):
        variants = self.variants.filter(is_available=True)

        prices = [v.price for v in variants if v.price is not None]
        mrps = [v.mrp for v in variants if v.mrp is not None]

        self.lowest_variant_price = min(prices) if prices else None
        self.lowest_variant_mrp = min(mrps) if mrps else None

        self.save(update_fields=["lowest_variant_price", "lowest_variant_mrp"])

    def save(self, *args, **kwargs):
        # generate slug ONLY if it doesn't exist
        if not self.slug:
            base_slug = "-".join(self.title.strip().split()).lower()
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
        if not self.is_available:
            self.variants.update(is_available=False)

class ProductMedia(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="media"
    )
    media = models.FileField(upload_to="products/")
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductMedia.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)

        # First media auto main
        if not ProductMedia.objects.filter(product=self.product).exists():
            self.is_main = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} Image"

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    # ✅ REQUIRED
    size = models.CharField(max_length=10)

    # ✅ OPTIONAL
    color = models.CharField(max_length=30, blank=True, null=True)
    image = models.ImageField(upload_to="variants/", blank=True, null=True)

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        blank=True,
        null=True
    )

    stock_qty = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'size', 'color')

    def clean(self):
        # ❌ size must exist
        if not self.size:
            raise ValidationError({"size": "Size is required."})

        # ❌ at least one of color OR image must exist
        if not self.color and not self.image:
            raise ValidationError(
                "Provide at least Color or Image for the variant."
            )

        # ✅ price validation
        if self.price and self.mrp and self.price > self.mrp:
            raise ValidationError({
                "price": "Price cannot be greater than MRP"
            })

        # ✅ fallback from product
        if not self.price and self.product.price:
            self.price = self.product.price

        if not self.mrp and self.product.mrp:
            self.mrp = self.product.mrp

        # ✅ stock → availability
        if self.stock_qty == 0:
            self.is_available = False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        if self.product:
            self.product.update_lowest_variant_prices()
            

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)

        if product:
            product.update_lowest_variant_prices()

    def __str__(self):
        if self.color:
            return f"{self.product.title} - {self.size} - {self.color}"
        return f"{self.product.title} - {self.size}"