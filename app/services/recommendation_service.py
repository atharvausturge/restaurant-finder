from app.schemas.recommendation import RecommendationSchema


def get_value(obj, field, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def filter_restaurants(restaurants, preferences):
    filtered_restaurants = []

    for restaurant in restaurants:
        if get_value(restaurant, "menu_available") is False:
            continue

        if preferences.max_travel_time_minutes is not None:
            travel_time = get_value(restaurant, "travel_time_minutes")
            if travel_time is None:
                continue
            if travel_time > preferences.max_travel_time_minutes:
                continue

        if get_value(restaurant, "is_open") is False:
            continue

        filtered_restaurants.append(restaurant)

    return filtered_restaurants

def serialize_restaurant(restaurant):
    return {
        "id": get_value(restaurant, "id"),
        "name": get_value(restaurant, "name"),
        "cuisine_type": get_value(restaurant, "cuisine_type"),
        "rating": get_value(restaurant, "rating"),
        "travel_time_minutes": get_value(restaurant, "travel_time_minutes"),
        "price_level": get_value(restaurant, "price_level"),
        "is_open": get_value(restaurant, "is_open"),
        "menu_available": get_value(restaurant, "menu_available"),
        "dietary_options": get_value(restaurant, "dietary_options", []) or [],
    }
    
def serialize_recommendation_menu_item(menu_item):
    return {
        "id": get_value(menu_item, "id"),
        "restaurant_id": get_value(menu_item, "restaurant_id"),
        "section_name": get_value(menu_item, "section_name", "Uncategorized"),
        "name": get_value(menu_item, "name"),
        "description": get_value(menu_item, "description"),
        "price": get_value(menu_item, "price"),
        "dietary_info": get_value(menu_item, "dietary_info", []) or [],
        "allergens": get_value(menu_item, "allergens", []) or [],
        "spice_level": get_value(menu_item, "spice_level"),
        "tags": get_value(menu_item, "tags", []) or [],
        "is_available": get_value(menu_item, "is_available", True),
        "short_summary": get_value(menu_item, "short_summary"),
    }

def collect_menu_items(menu_data):
    items = []

    for section_items in menu_data.values():
        items.extend(section_items)

    return items


def collect_menu_items_for_restaurant(restaurant, menu_items):
    items = []
    restaurant_id = get_value(restaurant, "id")

    for item in menu_items:
        if get_value(item, "restaurant_id") != restaurant_id:
            continue
        items.append(item)

    return items


def score_menu_item(menu_item, restaurant, preferences):
    score = 1

    if get_value(menu_item, "is_available") is False:
        return 0

    dietary_info = get_value(menu_item, "dietary_info", []) or []
    allergens = get_value(menu_item, "allergens", []) or []
    tags = get_value(menu_item, "tags", []) or []
    spice_level = get_value(menu_item, "spice_level")
    cuisine_type = get_value(restaurant, "cuisine_type", "")

    if preferences.dietary_restrictions:
        for restriction in preferences.dietary_restrictions:
            if restriction.lower() not in [info.lower() for info in dietary_info]:
                return 0
        score += 1

    if preferences.allergen_exclusions:
        for excluded in preferences.allergen_exclusions:
            if excluded.lower() in [a.lower() for a in allergens]:
                return 0

    if (
        preferences.spice_preference is not None
        and spice_level is not None
        and preferences.spice_preference.lower() == spice_level.lower()
    ):
        score += 2

    for tag in preferences.preferred_tags:
        if tag.lower() in [menu_tag.lower() for menu_tag in tags]:
            score += 1

    if cuisine_type.lower() in [cuisine.lower() for cuisine in preferences.cuisine_preferences]:
        score += 2

    return score


def score_restaurant(restaurant, scored_items, preferences):
    score = 0

    top_items = sorted(scored_items, key=lambda pair: pair[1], reverse=True)[:3]

    item_strength_sum = 0
    for item, item_score in top_items:
        item_strength_sum += item_score
    score += item_strength_sum

    rating = get_value(restaurant, "rating")
    if rating is not None:
        score += rating

    travel_time = get_value(restaurant, "travel_time_minutes")
    if travel_time is not None:
        if travel_time <= 10:
            score += 2
        elif travel_time <= 20:
            score += 1

    price_level = get_value(restaurant, "price_level")
    cuisine_type = get_value(restaurant, "cuisine_type", "")

    if (
        preferences.price_preference is not None
        and price_level is not None
        and preferences.price_preference.lower() == price_level.lower()
    ):
        score += 2

    if cuisine_type.lower() in [cuisine.lower() for cuisine in preferences.cuisine_preferences]:
        score += 2

    return score


def generate_reason(restaurant, top_items, preferences):
    reasons = []

    cuisine_type = get_value(restaurant, "cuisine_type", "")
    price_level = get_value(restaurant, "price_level")
    travel_time = get_value(restaurant, "travel_time_minutes")

    if cuisine_type.lower() in [cuisine.lower() for cuisine in preferences.cuisine_preferences]:
        reasons.append("it matches your preferred cuisine")

    if (
        preferences.price_preference is not None
        and price_level is not None
        and preferences.price_preference.lower() == price_level.lower()
    ):
        reasons.append("it fits your budget")

    if travel_time is not None and travel_time <= 10:
        reasons.append("it is nearby")

    if preferences.dietary_restrictions:
        has_matching_item = False

        for item, item_score in top_items:
            item_dietary = [info.lower() for info in (get_value(item, "dietary_info", []) or [])]

            if all(restriction.lower() in item_dietary for restriction in preferences.dietary_restrictions):
                has_matching_item = True
                break

        if has_matching_item:
            reasons.append("it has options that match your dietary needs")

    if preferences.allergen_exclusions:
        has_conflict = False
        excluded_lower = [a.lower() for a in preferences.allergen_exclusions]
        for item, _ in top_items:
            item_allergens = [a.lower() for a in (get_value(item, "allergens", []) or [])]
            if any(ex in item_allergens for ex in excluded_lower):
                has_conflict = True
                break
        if not has_conflict:
            reasons.append("it doesn't contain ingredients you're avoiding")

    if preferences.spice_preference is not None:
        if any(
            get_value(item, "spice_level") is not None
            and get_value(item, "spice_level").lower() == preferences.spice_preference.lower()
            for item, _ in top_items
        ):
            reasons.append("it has items that match your spice preference")

    item_names = [get_value(item, "name") for item, _ in top_items[:2] if get_value(item, "name")]
    if item_names:
        reasons.append("top matches include " + " and ".join(item_names))

    if not reasons:
        return "Recommended based on your preferences."

    return "Recommended because " + ", ".join(reasons) + "."


def generate_spoken_response(restaurant, top_items):
    parts = []

    name = get_value(restaurant, "name", "This restaurant")
    rating = get_value(restaurant, "rating")
    cuisine_type = get_value(restaurant, "cuisine_type")
    travel_time = get_value(restaurant, "travel_time_minutes")

    intro = name

    if rating is not None:
        intro += f" is rated {rating} stars"

    if cuisine_type:
        intro += f" and serves {cuisine_type} food"

    if travel_time is not None:
        intro += f". It is about {travel_time} minutes away."

    parts.append(intro)

    item_names = [get_value(item, "name") for item, _ in top_items[:2] if get_value(item, "name")]
    if item_names:
        if len(item_names) == 1:
            parts.append(f"A good option is {item_names[0]}.")
        else:
            parts.append(f"Recommended items include {item_names[0]} and {item_names[1]}.")

    return " ".join(parts)

    
def get_recommendations(restaurants, menu_items, preferences):
    filtered_restaurants = filter_restaurants(restaurants, preferences)
    recommendations = []

    for restaurant in filtered_restaurants:
        restaurant_items = collect_menu_items_for_restaurant(restaurant, menu_items)

        scored_items = []
        for menu_item in restaurant_items:
            item_score = score_menu_item(menu_item, restaurant, preferences)
            if item_score > 0:
                scored_items.append((menu_item, item_score))

        if not scored_items:
            continue

        top_items = sorted(scored_items, key=lambda pair: pair[1], reverse=True)[:3]

        restaurant_score = score_restaurant(restaurant, scored_items, preferences)
        reason = generate_reason(restaurant, top_items, preferences)
        spoken_response = generate_spoken_response(restaurant, top_items)

        recommended_menu_items = []
        for item, _ in top_items:
            recommended_menu_items.append(serialize_recommendation_menu_item(item))

        recommendation = RecommendationSchema(
            restaurant=serialize_restaurant(restaurant),
            recommended_items=recommended_menu_items,
            match_score=restaurant_score,
            reason=reason,
            spoken_response=spoken_response
        )

        recommendations.append(recommendation)

    recommendations.sort(key=lambda recommendation: recommendation.match_score, reverse=True)

    return recommendations[:3]