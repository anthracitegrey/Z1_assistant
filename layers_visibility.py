# Deploying:
# Save in /home/user/.config/GIMP/2.10/plug-ins/
# Restart GIMP. New menu items should appear.

# Freshly created document or edited step text manually?
# Consider running gimp_text_layer_set_text manually
# upon the 'step' text layer in Script-Fu console, just once.
# E.g. (gimp-text-layer-set-text 14 "123") ; substitute correct layer ID
# You can check the ID by opening "Edit Layer Attributes".

TOPMOST_OPACITY = 100 # percent
FADING_COLORS = ["#A0A0A0", "#FF0000", "#00FF00", "#0000FF"]
                # others     topmost    2nd        3rd

from gimpfu import *

def extract_relevant_groups(image):
    """
    Extracts group layers with names starting with "#<number>#".
    
    Parameters:
        image (gimp.Image): The image from which to extract relevant group layers.

    Returns:
        dict: Extracted label as key and GIMP group layer ID as value.
    """
    relevant_groups = {}
    
    for layer in image.layers:
        if pdb.gimp_item_is_group(layer):
            name = layer.name
            # Check if the name starts with "#" and has another "#" after a number.
            if name.startswith("#"):
                try:
                    # Extract the number between the "#" symbols without using regex.
                    end_index = name.index("#", 1)
                    label = int(name[1:end_index])
                    relevant_groups[label] = layer.ID
                except ValueError:
                    # Ignore groups with invalid formatting or non-numeric labels
                    continue
                except IndexError:
                    # Ignore cases where a closing "#" is not found
                    continue

    return relevant_groups

def adjacent_label(labels, current_step, direction):
    """
    Finds the adjacent label from a list of labels based on the direction.
    
    Parameters:
        labels (list): An unsorted list of labels (integers).
        current_step (int): The current step label to compare with.
        direction (bool): True means find the next larger, False means next smaller.
    
    Returns:
        int: The adjacent label based on the direction.

    Example Usage:
        print(adjacent_label([50, 10, 30], 42, False))  # 30
        print(adjacent_label([50, 10, 30], 77, True))   # 50
    """
    sorted_labels = sorted(labels)

    if direction:  # Find the next larger item
        for label in sorted_labels:
            if label > current_step:
                return label
        return sorted_labels[-1]  # Return the largest if no larger item is found
    else:  # Find the next smaller item
        for label in reversed(sorted_labels):
            if label < current_step:
                return label
        return sorted_labels[0]  # Return the smallest if no smaller item is found

def get_member_layer(group_layer, prefix):
    """
    Finds the first member layer in the group_layer
    whose name starts with the specified prefix.

    Parameters:
        group_layer (gimp.Item): Group layer to search through.
        prefix (string): Prefix to match (e.g., "color" or "hint").

    Returns:
        gimp.Item: The matched layer or None if not found.
    """
    for member in group_layer.children:
        if pdb.gimp_item_is_layer(member) and member.name.startswith(prefix):
            return member
    return None

def update_visibility(image, groups, step):
    """
    Updates visibility and appearance of group layers and their members based on the current step.

    Parameters:
        image (gimp.Image): The image object in GIMP.
        groups (dict): Dictionary mapping labels to group layer IDs.
        step (int): The current step value.
    """
    # Determine the labels of the next two layers below the current step
    labels = list(groups.keys())
    second_from_top = adjacent_label(labels, step, False)
    third_from_top = adjacent_label(labels, second_from_top, False)

    # At very low step values, there may be no 3rd or 2nd from top yet
    if third_from_top == second_from_top:
        third_from_top = None
    if second_from_top == step:
        second_from_top = None

    for label, group_id in groups.items():
        group_layer = gimp.Item.from_id(group_id)

        # Hide layers beyond current step
        if label > step:
            group_layer.visible = False
        else:
            # Show layers up to the current step
            group_layer.visible = True

            # Only the topmost layer is semi-transparent
            pdb.gimp_layer_set_opacity(group_layer,
                TOPMOST_OPACITY if label == step else 100)

            # Only show current step's hint (if such exists at all)
            hint_layer  = get_member_layer(group_layer, "hint")
            if hint_layer:
                hint_layer.visible = (label == step)

            color_layer = get_member_layer(group_layer, "color")
            if color_layer:
                # Set color and fill the color layer
                pdb.gimp_context_set_foreground(
                    FADING_COLORS[min(len(FADING_COLORS), max(
                        0, #all other layers
                        1 * (label == step),
                        2 * (label == second_from_top),
                        3 * (label == third_from_top)
                        ))]
                    )
                pdb.gimp_drawable_fill(color_layer, FILL_FOREGROUND)

def update_step(image, direction):
    """
    Incremenst or decrements "step".

    Parameters:
        image (gimp.Image): The image object in GIMP.
        direction (bool): True = next, False = previous.
    """
    # Find the text layer named "step"
    step_layer = None
    for layer in image.layers:
        if pdb.gimp_item_is_text_layer(layer) and layer.name == "step":
            step_layer = layer
            break

    if step_layer is None:
        raise ValueError("Text layer named 'step' not found in the image.")

    # Get the current step from the text layer's content
    try:
        current_step = int(pdb.gimp_text_layer_get_text(step_layer))
    except ValueError:
        raise ValueError("The text layer 'step' must contain a valid integer.")

    # Extract relevant groups from the image
    groups = extract_relevant_groups(image)

    # Find the new step among existing ones, in a given direction
    new_step = adjacent_label(list(groups.keys()), current_step, direction)

    # Update the "step" layer with the new step value
    pdb.gimp_text_layer_set_text(step_layer, str(new_step))

    update_visibility(image, groups, new_step)

def increase_step(image, drawable):
    update_step(image, True)
    pdb.gimp_displays_flush()

def decrease_step(image, drawable):
    update_step(image, False)
    pdb.gimp_displays_flush()

# Register the function in GIMP
# https://www.gimp.org/docs/python/
register(
    "python-fu-increase-step",
    "Vorheriger Aufbauschritt",
    "Lorem ipsum",
    "Author", "Copyright", "2024",
    "<Image>/Python-Fu/Aufbauschritt vor",
    "*",  # Image type, "*" means all types
    [],
    [],
    increase_step
)

register(
    "python-fu-decrease-step",
    "Naechster Aufbauschritt",
    "Lorem ipsum",
    "Author", "Copyright", "2024",
    "<Image>/Python-Fu/Aufbauschritt zurueck",
    "*",  # Image type, "*" means all types
    [],
    [],
    decrease_step
)

main()
