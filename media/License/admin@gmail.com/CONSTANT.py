TRIP_STATUS = (
    ("Pending", "Pending"),
    ("InProgress", "InProgress"),
    ("Completed", "Completed"),
    ("Rejected", "Rejected"),
    ("Cancelled", "Cancelled"),
)

ORDER_STATUS = (
    ("Pending", "Pending"),
    ("InProgress", "InProgress"),
    ("Confirmed", "Confirmed"),
    ("Rejected", "Rejected"),
    ("Cancelled", "Cancelled"),
    ("Completed", "Completed"),
    ("Refund", "Refund")
)

PAYMENT_STATUS = (
    ("Pending", "Pending"),
    ("InProgress", "InProgress"),
    ("Paid", "Paid"),
    ("Rejected", "Rejected"),
    ("Cancelled", "Cancelled"),
)
ROUTE_TYPES = (
    ("on_going", "On going"),
    ("return_back", "Return Back"),
)

BUS_CHARGES_SCALE = (
    # ("Hour", "hour"),
    # ("Day", "day"),    
    ("Kilometer", "kilometer"),
)

FAQ_TYPE = (
    ("cancellation", "cancellation"),
    ("payment", "payment"),
    ("booking details", "booking details"),
    ("communication", "communication"),
    ("credit cards", "credit cards"),
    ("security and awareness", "security and awareness"),

)

BUS_TAGS = (

    ("BESTSELLER", "BESTSELLER"),
    ("FEATURED", "FEATURED"),
    ("NEW", "NEW"),
    ("POPULAR", "POPULAR"),
    ("SALE", "SALE"),
    ("UPCOMING", "UPCOMING"),  # Add a new choice "UPCOMING"
    ("LAST_MINUTE", "LAST MINUTE"),  # Add a new choice "LAST MINUTE"
    ("DISCOUNTED", "DISCOUNTED"),  # Add a new choice "DISCOUNTED"
    # Add more choices as needed
)

BUS_STATUS = (

    ("Available", "Available"),
    ("Reserved", "Reserved"),
    ("Booked", "Booked"),

)

LICENSE_STATUS = (

    ("Pending", "Pending"),
    ("InProgress", "InProgress"),
    ("Verified", "Verified"),
    ("NotVerified", "NotVerified"),

)

BUS_FILTERS = {
    "2": "NEW",
    "3": "POPULAR",
    "4": "BESTSELLER",
    "5": "FEATURED",
}

BUS_FILTER_SORT = {
    "1": "id",
    "6": "per_scale_charges",
    "7": "-per_scale_charges",
    "8": "name",
    "9": "-name",
}

PAYMENT_GATEWAYS = (
    ("Stripe", "Stripe"),
    ("Cash", "Cash"),
)
