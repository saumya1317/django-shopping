from django.db import models
from django.contrib.auth.models import User
# Create your models here.
CATEGORY_CHOICES = (
    ('D', 'Dresses'),
    ('J', 'Jeans/Denims'),
    ('B', 'Beauty'),
    ('P', 'Party Dress'),
    ('E', 'Ethnic Dress'),
    ('F', 'Food'),  # Added food category
)
STATE_CHOICES = (
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Delhi', 'Delhi'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
)

class Product(models.Model):
    title = models.CharField(max_length= 100)
    selling_price = models.FloatField()
    discounted_price = models.FloatField()
    description =  models.TextField()
    prodapp = models.TextField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='products_new')
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override save so that whenever the discounted_price of a product
        drops we can automatically:
        1. Notify users who created a PriceAlert whose target_price is now
           reached (<= discounted_price).
        2. If the alert has buy_when_drop=True, add the product to the
           user's cart automatically.

        NOTE:  ‑ This is kept extremely simple and synchronous.  In a real
        world app you would off-load the fulfilment/notification work to a
        background task queue (Celery, RQ, etc.).
        """
        from django.utils import timezone  # local import to avoid circulars
        # Determine previous discounted_price (if any)
        old_price = None
        if self.pk:
            try:
                old_price = Product.objects.values_list('discounted_price', flat=True).get(pk=self.pk)
            except Product.DoesNotExist:
                old_price = None

        super().save(*args, **kwargs)  # Save first so self has the new price

        # Only act if the price actually decreased
        if old_price is not None and self.discounted_price < old_price:
            from django.db import transaction

            try:
                from .models import PriceAlert  # late import
            except ImportError:
                return

            alert_ids = list(
                PriceAlert.objects.filter(
                    product=self,
                    fulfilled=False,
                    target_price__gte=self.discounted_price,
                ).values_list('id', flat=True)
            )

            if not alert_ids:
                return

            from .tasks import process_price_alert

            def _dispatch_tasks():
                for aid in alert_ids:
                    try:
                        process_price_alert.delay(aid, self.discounted_price)
                    except Exception:
                        process_price_alert(aid, self.discounted_price)

            # Ensure tasks are queued only after the outer transaction commits,
            # preventing a second process (Celery worker) from writing while
            # SQLite still holds the lock.
            transaction.on_commit(_dispatch_tasks)

class Customer(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=200) 
    locality = models.CharField(max_length=200) 
    city =  models.CharField(max_length=50)
    mobile = models.IntegerField(default=0)
    zipcode = models.IntegerField()
    state = models.CharField(choices=STATE_CHOICES,max_length=100)
    def __str__(self):
        return self.name

# ---------------------------------------------------------------------------
#  PRICE ALERTS
# ---------------------------------------------------------------------------

class PriceAlert(models.Model):
    """A user-defined desired price for a product."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    target_price = models.FloatField(help_text="Desired price at which to be notified/buy")
    buy_when_drop = models.BooleanField(
        default=False,
        help_text="If checked, the product will be automatically added to cart once the target price is reached",
    )
    fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        status = "fulfilled" if self.fulfilled else "pending"
        return f"{self.user}:{self.product} @ ₹{self.target_price} ({status})"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete= models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price