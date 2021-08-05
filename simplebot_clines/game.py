from random import randint, randrange, sample
from typing import Optional

CELL = ["⬜", "🔴", "🟢", "🟡", "🔵", "🟣", "🟠", "🟤"]
COLS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
ROWS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮"]


class Board:
    def __init__(self, game: str = None, old_score: int = 0) -> None:
        if game:
            lines = game.split("\n")
            self.score = int(lines.pop(0))
            self.old_score = int(lines.pop(0))
            self.game = Field(balls=lines.pop(0), board=lines.pop(0))
        else:
            self.score = 0
            self.old_score = old_score
            self.game = Field()
            self.game.set_next_balls()

    def export(self) -> str:
        board = str(self.score) + "\n"
        board += str(self.old_score) + "\n"
        board += "".join(str(b.color) for b in self.game.next_balls)
        board += "\n"
        for row in self.game.field:
            for ball in row:
                if ball is None:
                    board += "0"
                else:
                    board += str(ball.color)
        return board

    def __str__(self) -> str:
        text = "|".join(COLS) + "\n"
        for i, row in enumerate(self.game.field):
            for d in row:
                text += CELL[0] if d is None else CELL[d.color]
                text += "|"
            text += "{}\n".format(ROWS[i])

        return text

    def update_score(self):
        self.score += self.game.score
        self.game.score = 0

    @staticmethod
    def get_position(coord) -> tuple:
        sorted_coord = sorted(coord.lower())
        x = "123456789".find(sorted_coord[0])
        y = "abcdefghi".find(sorted_coord[1])
        return (x, y)

    def move(self, coords: str) -> None:
        x1, y1 = self.get_position(coords[:2])
        x2, y2 = self.get_position(coords[2:])

        if not self.game.try_move(x1, y1, x2, y2):
            raise ValueError("Invalid move")

        self.game.make_step(x1, y1, x2, y2)

        balls = self.game.find_full_lines(x2, y2)
        if balls:
            self.game.delete_full_lines(balls)
            self.update_score()
        else:
            self.next()

    def next(self) -> None:
        self.game.set_next_balls()
        for e in self.game.set_balls:
            array = self.game.find_full_lines(e[0], e[1])
            if array:
                self.game.delete_full_lines(array)
        self.update_score()

    def result(self) -> int:
        if self.game.free_cells:
            return 0
        return 1


class Ball:
    """Class implementing a ball object"""

    def __init__(self, color: int = 0) -> None:
        """Initialize a ball object"""
        self.color = color
        self.selected = False

    def __eq__(self, other) -> bool:
        """Define the equality of balls"""
        return self.color == other.color

    def set_color(self, color: int) -> None:
        """Set the color (number) of the ball"""
        self.color = color

    def set_random_color(self, number_of_colors: int) -> None:
        """Determine the color of the ball"""
        self.color = randint(1, number_of_colors)


class Field:
    """Game Field"""

    def __init__(
        self,
        amount_cells: int = 9,
        player: str = "Player",
        balls: str = None,
        board: str = None,
    ) -> None:
        """Initialize game field"""
        self.height = amount_cells
        self.width = amount_cells
        self.player = player
        self._set_number_of_ball_per_line()
        self._set_number_of_next_ball()
        self._set_number_of_color()
        self._init_field(board)

        if balls is not None:
            self.next_balls = []
            for e in balls:
                ball = Ball()
                ball.set_color(int(e))
                self.next_balls.append(ball)
        else:
            self.next_balls = []
            self.make_next_balls()

        self.set_balls: list = []
        self.score = 0

    def _init_field(self, board: Optional[str]) -> None:
        """Initialize field"""
        if board is not None:
            self.field: list = []
            self.free_cells = []
            for i in range(self.height):
                self.field.append([])
                for j in range(self.width):
                    if board[i * self.height + j] == "0":
                        self.field[i].append(None)
                        self.free_cells.append((j, i))
                    else:
                        ball = Ball()
                        ball.set_color(int(board[i * self.height + j]))
                        self.field[i].append(ball)
        else:
            self.field = []
            self.free_cells = []
            for rows in range(self.height):
                self.field.append([])
                for columns in range(self.width):
                    self.field[rows].append(None)
                    self.free_cells.append((columns, rows))

    def _set_number_of_color(self) -> None:
        """Set number of color"""
        self.number_of_color = self.height // 2 + 3

    def _set_number_of_ball_per_line(self) -> None:
        """Set number of a ball per line"""
        self.balls_in_line = self.height // 3 + 2

    def _set_number_of_next_ball(self) -> None:
        """Set the number of a ball put on the field"""
        self.number_of_next_ball = self.height // 4 + 1

    def make_next_balls(self) -> None:
        """Set the following balls"""
        self.next_balls.clear()
        for _ in range(self.number_of_next_ball):
            ball = Ball()
            ball.set_random_color(self.number_of_color)
            self.next_balls.append(ball)

    def clear_field(self) -> None:
        """Clear the game field"""
        self.free_cells.clear()
        for rows in range(self.height):
            for columns in range(self.width):
                self.field[rows][columns] = None
                self.free_cells.append((rows, columns))

    def refresh_field(self) -> None:
        """Return the field to its initial state"""
        self.clear_field()
        self.score = 0
        self.make_next_balls()
        self.set_next_balls()

    def get_ball(self, x: int, y: int) -> Optional[Ball]:
        """Get a ball by coordinates"""
        return self.field[y][x]

    def get_color_of_ball(self, x: int, y: int) -> Optional[int]:
        """Get the color of the ball be coordinates"""
        if self.field[y][x] is not None:
            return self.field[y][x].color
        return None

    def set_ball(self, x: int, y: int, ball: Ball) -> None:
        """Set the ball by coordinates"""
        self.field[y][x] = ball
        self.free_cells.remove((x, y))

    def delete_ball(self, x: int, y: int) -> None:
        """Delete a ball by coordinates"""
        self.field[y][x] = None
        self.free_cells.append((x, y))

    def set_next_balls(self) -> None:
        """install the next balls on field"""
        k = len(self.free_cells)
        if k < self.number_of_next_ball:
            balls = sample(self.next_balls, k=k)
        else:
            balls = self.next_balls
        self.set_balls.clear()
        for ball in balls:
            pos = randrange(0, len(self.free_cells))
            coordinates = self.free_cells[pos]
            self.set_ball(coordinates[0], coordinates[1], ball)
            self.set_balls.append((coordinates[0], coordinates[1]))
        self.make_next_balls()

    def try_move(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Try move ball in needed coordinate"""
        if (
            self.get_ball(end_x, end_y) is not None
            or self.get_ball(start_x, start_y) is None
        ):
            return False
        queue = []
        visited_cells = []
        queue.append((start_x, start_y))
        while len(queue) != 0:
            coords = queue.pop(0)
            if (
                coords[0] < 0
                or coords[0] >= self.height
                or coords[1] < 0
                or coords[1] >= self.width
            ):
                continue
            has_ball = self.get_ball(coords[0], coords[1]) is not None
            if (coords != (start_x, start_y) and has_ball) or (
                coords[0],
                coords[1],
            ) in visited_cells:
                continue
            if coords[0] == end_x and coords[1] == end_y:
                return True
            visited_cells.append((coords[0], coords[1]))
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if 0 in (dx, dy):
                        queue.append((coords[0] + dx, coords[1] + dy))
        return False

    def make_step(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """Make step"""
        ball = Ball(self.get_ball(start_x, start_y).color)
        self.set_ball(end_x, end_y, ball)
        self.delete_ball(start_x, start_y)

    def find_full_lines(self, x: int, y: int) -> list:
        """Find all full lines starting by coordinates of ball"""
        if self.get_ball(x, y) is None:
            return []
        balls = []
        current_color = self.get_color_of_ball(x, y)
        ball_for_delete = []
        minus_dx = x
        plus_dx = x + 1
        while minus_dx >= 0 and self.get_color_of_ball(minus_dx, y) == current_color:
            ball_for_delete.append((minus_dx, y))
            minus_dx -= 1
        while (
            plus_dx < self.width and self.get_color_of_ball(plus_dx, y) == current_color
        ):
            ball_for_delete.append((plus_dx, y))
            plus_dx += 1
        if len(ball_for_delete) >= self.balls_in_line:
            balls.extend(ball_for_delete)
        ball_for_delete.clear()
        minus_dy = y
        plus_dy = y + 1
        while minus_dy >= 0 and self.get_color_of_ball(x, minus_dy) == current_color:
            ball_for_delete.append((x, minus_dy))
            minus_dy -= 1
        while (
            plus_dy < self.height
            and self.get_color_of_ball(x, plus_dy) == current_color
        ):
            ball_for_delete.append((x, plus_dy))
            plus_dy += 1
        if len(ball_for_delete) >= self.balls_in_line:
            balls.extend(ball_for_delete)
        ball_for_delete.clear()
        minus_dx = x
        minus_dy = y
        plus_dx = x + 1
        plus_dy = y + 1
        while (
            minus_dx >= 0
            and minus_dy >= 0
            and self.get_color_of_ball(minus_dx, minus_dy) == current_color
        ):
            ball_for_delete.append((minus_dx, minus_dy))
            minus_dx -= 1
            minus_dy -= 1
        while (
            plus_dx < self.width
            and plus_dy < self.height
            and self.get_color_of_ball(plus_dx, plus_dy) == current_color
        ):
            ball_for_delete.append((plus_dx, plus_dy))
            plus_dx += 1
            plus_dy += 1
        if len(ball_for_delete) >= self.balls_in_line:
            balls.extend(ball_for_delete)
        ball_for_delete.clear()
        minus_dx = x
        plus_dy = y
        while (
            minus_dx >= 0
            and plus_dy < self.height
            and self.get_color_of_ball(minus_dx, plus_dy) == current_color
        ):
            ball_for_delete.append((minus_dx, plus_dy))
            minus_dx -= 1
            plus_dy += 1
        plus_dx = x + 1
        minus_dy = y - 1
        while (
            plus_dx < self.width
            and minus_dy >= 0
            and self.get_color_of_ball(plus_dx, minus_dy) == current_color
        ):
            ball_for_delete.append((plus_dx, minus_dy))
            plus_dx += 1
            minus_dy -= 1
        if len(ball_for_delete) >= self.balls_in_line:
            balls.extend(ball_for_delete)
        return balls

    def delete_full_lines(self, array_of_balls_coord: list) -> None:
        """Delete full lines"""
        if array_of_balls_coord:
            self.scoring(len(array_of_balls_coord))
            for coordinate in array_of_balls_coord:
                self.delete_ball(*coordinate)

    def scoring(self, length_of_remote_line: int) -> None:
        """Scoring by length of remote line"""
        multiplier = length_of_remote_line - self.balls_in_line + 1
        self.score += 10 * length_of_remote_line * multiplier
