document.addEventListener('DOMContentLoaded', () => {
    const step1 = document.getElementById('step-1-restaurant');
    const step2 = document.getElementById('step-2-menu');
    const btnStart = document.getElementById('btn-start-menu');

    const restNameInput = document.getElementById('restaurant-name');
    const restLocInput = document.getElementById('restaurant-location');
    const displayRestInfo = document.getElementById('display-restaurant-info');

    const tabBtns = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.menu-section');

    const btnAddItems = document.querySelectorAll('.btn-add-item');
    const itemTemplate = document.getElementById('item-template');

    const suggestionsBox = document.getElementById('location-suggestions');

    let debounceTimeout;
    restLocInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimeout);
        const query = e.target.value.trim();

        if (query.length < 3) {
            suggestionsBox.style.display = 'none';
            return;
        }

        debounceTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/discover/places/autocomplete?query=${encodeURIComponent(query)}`);

                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();

                suggestionsBox.innerHTML = '';
                if (data.places && data.places.length > 0) {
                    suggestionsBox.style.display = 'block';
                    data.places.forEach(place => {
                        const li = document.createElement('li');
                        li.style.padding = '8px';
                        li.style.cursor = 'pointer';
                        li.style.borderBottom = '1px solid #eee';

                        const name = place.displayName?.text || '';
                        const address = place.formattedAddress || '';
                        li.textContent = `${name} - ${address}`;

                        li.addEventListener('click', () => {
                            restLocInput.value = address;
                            restNameInput.value = name;
                            restLocInput.dataset.placeId = place.id;
                            suggestionsBox.style.display = 'none';
                        });

                        // hover effect
                        li.addEventListener('mouseenter', () => li.style.backgroundColor = '#f0f0f0');
                        li.addEventListener('mouseleave', () => li.style.backgroundColor = 'transparent');

                        suggestionsBox.appendChild(li);
                    });
                } else {
                    suggestionsBox.style.display = 'none';
                }
            } catch (error) {
                console.error('Error fetching places:', error);
            }
        }, 500);
    });

    document.addEventListener('click', (e) => {
        if (e.target !== restLocInput && e.target !== suggestionsBox) {
            suggestionsBox.style.display = 'none';
        }
    });

    btnStart.addEventListener('click', () => {
        const name = restNameInput.value.trim();
        const loc = restLocInput.value.trim();
        if (!name || !loc) {
            alert('Please enter both restaurant name and location.');
            return;
        }

        displayRestInfo.textContent = `${name} - ${loc} Menu Builder`;
        step1.style.display = 'none';
        step2.style.display = 'block';
    });

    const menuSections = document.getElementById('menu-sections');
    const btnAddSection = document.getElementById('btn-add-section');
    const sectionTemplate = document.getElementById('section-template');

    btnAddSection.addEventListener('click', () => {
        const clone = document.importNode(sectionTemplate.content, true);
        const sectionDiv = clone.querySelector('.menu-section');

        clone.querySelector('.btn-remove-section').addEventListener('click', (e) => {
            e.target.closest('.menu-section').remove();
        });

        const container = clone.querySelector('.items-container');
        clone.querySelector('.btn-add-item').addEventListener('click', () => {
            const itemClone = document.importNode(itemTemplate.content, true);
            itemClone.querySelector('.btn-remove-item').addEventListener('click', (e) => {
                e.target.closest('.menu-item-form').remove();
            });
            container.appendChild(itemClone);
        });

        menuSections.appendChild(clone);
    });

    // Save Menu
    document.getElementById('btn-submit-menu').addEventListener('click', async () => {
        const name = restNameInput.value.trim();
        const loc = restLocInput.value.trim();

        const restaurant_id = restLocInput.dataset.placeId || "rest_" + Math.random().toString(36).substring(2, 9);

        const menuItems = [];

        const sections = document.querySelectorAll('#menu-sections .menu-section');
        sections.forEach(section => {
            const sectionName = section.querySelector('.section-title').value.trim();
            if (!sectionName) return;

            const items = section.querySelectorAll('.menu-item-form');
            items.forEach(item => {
                const itemName = item.querySelector('.item-name').value.trim();
                const itemPrice = parseFloat(item.querySelector('.item-price').value);
                const itemDesc = item.querySelector('.item-desc').value.trim();
                const itemDietary = item.querySelector('.item-dietary').value.split(',').map(s => s.trim()).filter(s => s);

                const spiceLevelMap = ["mild", "medium", "spicy", "very spicy"];
                const spiceLevelVal = parseInt(item.querySelector('.item-spice').value);
                const spiceLevel = spiceLevelMap[spiceLevelVal] || "mild";

                const allergens = [];
                item.querySelectorAll('.allergens-grid input[type="checkbox"]:checked').forEach(cb => {
                    allergens.push(cb.value);
                });

                if (itemName) {
                    menuItems.push({
                        id: "item_" + Math.random().toString(36).substring(2, 9),
                        restaurant_id: restaurant_id,
                        section_name: sectionName,
                        name: itemName,
                        description: itemDesc || null,
                        price: isNaN(itemPrice) ? null : itemPrice,
                        dietary_info: itemDietary,
                        allergens: allergens,
                        spice_level: spiceLevel,
                        tags: [],
                        is_available: true
                    });
                }
            });
        });

        if (menuItems.length === 0) {
            alert("Please add at least one menu item.");
            return;
        }

        try {
            const response = await fetch(`/restaurants/menus/bulk?restaurant_name=${encodeURIComponent(name)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(menuItems)
            });

            if (response.ok) {
                alert('Menu saved successfully!');
            } else {
                throw new Error("Failed to save menu");
            }
        } catch (error) {
            console.error('Error saving menu:', error);
            alert('Failed to save menu. Check console for details.');
        }
    });
});