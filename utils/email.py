import threading
from django.core.mail import EmailMessage
from django.conf import settings


def _send_email_async(email):
    email.send(fail_silently=False)


def send_admin_order_email(orders):
    # ✅ normalize to list
    if not isinstance(orders, (list, tuple)):
        orders = [orders]

    first_order = orders[0]

    subject = f"🛒 New Order Received | {len(orders)} Item(s)"

    product_block = ""
    grand_total = 0

    for i, order in enumerate(orders, start=1):
        grand_total += float(order.total)

        product_block += f"""
ITEM #{i}
---------

Product Name : {order.product_name}
Product Slug : {order.product_slug}
Size         : {order.size or "N/A"}
Quantity     : {order.qty}

MRP          : ₹{order.mrp}
Discount     : ₹{order.discount}
Price        : ₹{order.price}
Delivery Fee : ₹{order.delivery_charge}

Item Total   : ₹{order.total}
"""

    message = f"""
NEW ORDER RECEIVED | {len(orders)} ITEMS
==================

ORDER INFO

Payment Method  : {first_order.payment_method.upper()}
Payment Status  : {first_order.payment_status.upper()}
Payment Channel : {first_order.payment_channel or "N/A"}

RAZORPAY DETAILS

Razorpay Order ID   : {first_order.razorpay_order_id or "N/A"}
Razorpay Payment ID : {first_order.razorpay_payment_id or "N/A"}

PRODUCT DETAILS
{product_block}

------------------
GRAND TOTAL: ₹{grand_total}
------------------

CUSTOMER DETAILS

Name      : {first_order.name}
Email     : {first_order.user.email if first_order.user and first_order.user.email else "Not provided"}
Phone     : {first_order.phone}
Alt Phone : {first_order.alt_phone or "Not provided"}

DELIVERY ADDRESS

Address  : {first_order.address_line or "Not Provided"}
Location : {first_order.location}
City     : {first_order.city}, {first_order.state}
Pincode  : {first_order.pincode}
Landmark : {first_order.landmark or "Not Provided"}

=====================
This is an automated order alert.
"""

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ORDER_NOTIFICATION_EMAIL],
    )

    threading.Thread(
        target=_send_email_async,
        args=(email,),
        daemon=True
    ).start()
