import random
import typing


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "Adrian",  # TODO: Your Battlesnake Username
        "color": "#0044ff",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    my_head = game_state["you"]["head"]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"
    my_body = game_state["you"]["body"]  # Coordinates of your body
    board_width = game_state["board"]["width"]
    board_height = game_state["board"]["height"]
    opponents = game_state["board"]["snakes"]
    opponents.pop(0)
    food = game_state["board"]["food"]

    free_squares = calculate_free_squares(board_height, board_width, my_body, opponents)
    target_length = len(free_squares) // 2

    find_safe_moves(board_height, board_width, is_move_safe, my_body, my_head, my_neck, opponents)
    avoid_tunnels(board_height, board_width, is_move_safe, my_body, my_head, opponents)
    avoid_head_on_collision(my_head, opponents, is_move_safe)
    avoid_adjacent_head_following(my_head, opponents, is_move_safe)

    if len(my_body) < target_length:
        food_move = move_towards_food(food, my_head, is_move_safe)
        if food_move:
            return food_move

    # Are there any safe moves left?
    safe_moves = [move for move, is_safe in is_move_safe.items() if is_safe]

    if not safe_moves:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    # Choose a random move from the safe ones
    next_move = random.choice(safe_moves)

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}

def move_towards_food(food, my_head, is_move_safe):
    # Move towards food if possible
    def distance(point1, point2):
        return abs(point1["x"] - point2["x"]) + abs(point1["y"] - point2["y"])

    if food:
        closest_food = min(food, key=lambda f: distance(my_head, f))
        if closest_food["x"] < my_head["x"] and is_move_safe["left"]:
            return {"move": "left"}
        if closest_food["x"] > my_head["x"] and is_move_safe["right"]:
            return {"move": "right"}
        if closest_food["y"] < my_head["y"] and is_move_safe["down"]:
            return {"move": "down"}
        if closest_food["y"] > my_head["y"] and is_move_safe["up"]:
            return {"move": "up"}

    return None

def calculate_free_squares(board_height, board_width, my_body, opponents):
    occupied_squares = set((segment["x"], segment["y"]) for segment in my_body)
    for snake in opponents:
        for segment in snake["body"]:
            occupied_squares.add((segment["x"], segment["y"]))

    free_squares = []
    for x in range(board_width):
        for y in range(board_height):
            if (x, y) not in occupied_squares:
                free_squares.append((x, y))

    return free_squares

def find_safe_moves(board_height, board_width, is_move_safe, my_body, my_head, my_neck, opponents):
    # Prevent moving backwards
    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False
    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False
    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False
    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False
    # Prevent moving out of bounds
    if my_head["x"] == 0:
        is_move_safe["left"] = False
    if my_head["x"] == board_width - 1:
        is_move_safe["right"] = False
    if my_head["y"] == 0:
        is_move_safe["down"] = False
    if my_head["y"] == board_height - 1:
        is_move_safe["up"] = False
    # Prevent colliding with itself
    for segment in my_body:
        if {"x": my_head["x"], "y": my_head["y"] + 1} == segment:
            is_move_safe["up"] = False
        if {"x": my_head["x"], "y": my_head["y"] - 1} == segment:
            is_move_safe["down"] = False
        if {"x": my_head["x"] - 1, "y": my_head["y"]} == segment:
            is_move_safe["left"] = False
        if {"x": my_head["x"] + 1, "y": my_head["y"]} == segment:
            is_move_safe["right"] = False
    # Prevent colliding with other snakes
    for snake in opponents:
        for segment in snake["body"]:
            if {"x": my_head["x"], "y": my_head["y"] + 1} == segment:
                is_move_safe["up"] = False
            if {"x": my_head["x"], "y": my_head["y"] - 1} == segment:
                is_move_safe["down"] = False
            if {"x": my_head["x"] - 1, "y": my_head["y"]} == segment:
                is_move_safe["left"] = False
            if {"x": my_head["x"] + 1, "y": my_head["y"]} == segment:
                is_move_safe["right"] = False

def avoid_tunnels(board_height, board_width, is_move_safe, my_body, my_head, opponents):
    # Prevent entering narrow tunnels
    def is_tunnel(x, y):
        walls = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx < 0 or ny < 0 or nx >= board_width or ny >= board_height or
                {"x": nx, "y": ny} in my_body or
                any({"x": nx, "y": ny} in snake["body"] for snake in opponents)):
                walls += 1
        return walls >= 3  # A tunnel is a square with 3 or more walls around it

    # Check each move for tunnels
    if is_move_safe["up"] and is_tunnel(my_head["x"], my_head["y"] + 1):
        is_move_safe["up"] = False
    if is_move_safe["down"] and is_tunnel(my_head["x"], my_head["y"] - 1):
        is_move_safe["down"] = False
    if is_move_safe["left"] and is_tunnel(my_head["x"] - 1, my_head["y"]):
        is_move_safe["left"] = False
    if is_move_safe["right"] and is_tunnel(my_head["x"] + 1, my_head["y"]):
        is_move_safe["right"] = False

def avoid_head_on_collision(my_head, opponents, is_move_safe):
    # Prevent head-on collisions with other snakes
    for snake in opponents:
        snake_head = snake["head"]
        potential_next_positions = [
            {"x": snake_head["x"], "y": snake_head["y"] + 1},  # Snake moving up
            {"x": snake_head["x"], "y": snake_head["y"] - 1},  # Snake moving down
            {"x": snake_head["x"] - 1, "y": snake_head["y"]},  # Snake moving left
            {"x": snake_head["x"] + 1, "y": snake_head["y"]}   # Snake moving right
        ]

        if {"x": my_head["x"], "y": my_head["y"] + 1} in potential_next_positions:
            is_move_safe["up"] = False
        if {"x": my_head["x"], "y": my_head["y"] - 1} in potential_next_positions:
            is_move_safe["down"] = False
        if {"x": my_head["x"] - 1, "y": my_head["y"]} in potential_next_positions:
            is_move_safe["left"] = False
        if {"x": my_head["x"] + 1, "y": my_head["y"]} in potential_next_positions:
            is_move_safe["right"] = False

def avoid_adjacent_head_following(my_head, opponents, is_move_safe):
    # Prevent moving directly behind another snake's head
    for snake in opponents:
        snake_head = snake["head"]
        snake_body = snake["body"]

        # Check if my head is directly behind the other snake's head in its movement direction
        if {"x": my_head["x"], "y": my_head["y"] + 1} == snake_head and {"x": my_head["x"], "y": my_head["y"] + 2} not in snake_body:
            is_move_safe["up"] = False
        if {"x": my_head["x"], "y": my_head["y"] - 1} == snake_head and {"x": my_head["x"], "y": my_head["y"] - 2} not in snake_body:
            is_move_safe["down"] = False
        if {"x": my_head["x"] - 1, "y": my_head["y"]} == snake_head and {"x": my_head["x"] - 2, "y": my_head["y"]} not in snake_body:
            is_move_safe["left"] = False
        if {"x": my_head["x"] + 1, "y": my_head["y"]} == snake_head and {"x": my_head["x"] + 2, "y": my_head["y"]} not in snake_body:
            is_move_safe["right"] = False

# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
