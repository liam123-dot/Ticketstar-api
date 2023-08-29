def my_round(value, decimal_places=2):
    offset = 10 ** -decimal_places / 2
    return round(value + offset, decimal_places)


print(my_round((3 * 0.015) + 0.2))
