from app.repositories import menu_repository as repository


def group_menu_items_by_section(menu_items):
    grouped_menu = {}

    for item in menu_items:
        section_name = item.section_name or "Uncategorized"
        if section_name not in grouped_menu:
            grouped_menu[section_name] = []
        grouped_menu[section_name].append(serialize_menu_item(item))

    return grouped_menu


def serialize_menu_item(menu_item):
    return {
        "id": menu_item.id,
        "name": menu_item.name,
        "description": menu_item.description,
        "price": menu_item.price,
        "section_name": menu_item.section_name,
        "restaurant_id": menu_item.restaurant_id,
        "is_available": menu_item.is_available,
        "dietary_info": menu_item.dietary_info,
        "allergens": getattr(menu_item, "allergens", []) or [],
        "spice_level": menu_item.spice_level,
        "tags": menu_item.tags,
    }


def get_restaurant_menu(restaurant_id):
    menu_items = repository.get_menu_by_restaurant_id(restaurant_id)

    if not menu_items:
        return {
            "restaurant_id": restaurant_id,
            "menu": {}
        }

    grouped_menu = group_menu_items_by_section(menu_items)

    return {
        "restaurant_id": restaurant_id,
        "menu": grouped_menu
    }