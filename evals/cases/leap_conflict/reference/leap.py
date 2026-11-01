def is_leap(year):
    """Return True if `year` is a Gregorian leap year (see README)."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
