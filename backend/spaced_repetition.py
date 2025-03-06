def update_card(card, quality: int):
    # SM2 Algorithm: Update interval and ease factor
    if quality >= 3:
        if card["interval"] == 1:
            card["interval"] = 6
        else:
            card["interval"] *= card["ease"]
        card["ease"] = max(1.3, card["ease"] + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    else:
        card["interval"] = 1
    return card