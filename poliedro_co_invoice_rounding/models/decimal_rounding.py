from decimal import Decimal, ROUND_HALF_UP


def round_to_increment(amount, increment, quantum=None):
    """Round a decimal amount to a multiple using ROUND_HALF_UP.

    Inputs from Odoo are floats, so ``str`` is used to preserve their displayed
    decimal value instead of importing the binary float approximation.
    """
    amount = Decimal(str(amount))
    increment = Decimal(str(increment))
    rounded = (amount / increment).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * increment
    if quantum:
        rounded = rounded.quantize(Decimal(str(quantum)), rounding=ROUND_HALF_UP)
    return rounded

