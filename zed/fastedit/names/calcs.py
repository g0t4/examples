



def calc(l, r, y):
    mr = r / 100 / 12
    tp = y * 12

    mp = (l * mr * (1 + mr) ** tp) / ((1 + mr) ** tp - 1)
    t = mp * tp

    return round(mp, 2), round(t, 2)

print(calc(200_000, 6, 15))
